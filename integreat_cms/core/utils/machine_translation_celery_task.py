from __future__ import annotations

import contextlib
import logging
from collections import defaultdict
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from celery import shared_task, Task
from django.apps import apps
from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.http import HttpRequest
from django.utils.translation import (
    activate as activate_language,
)
from django.utils.translation import (
    get_language,
    gettext,
)
from django.utils.translation import (
    gettext_lazy as _,
)

from ...cms.models.regions.region import Region
from ...cms.models.users.user import User
from ...deepl_api.deepl_api_client import DeepLApiClient
from ...google_translate_api.google_translate_api_client import GoogleTranslateApiClient

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.forms.models import ModelFormMetaclass

    from ...cms.utils.machine_translation_types import ObjectIdAndLanguageSlug
    from .machine_translation_api_client import MachineTranslationApiClient

logger = logging.getLogger(__name__)


_API_CLIENTS: dict[str, type[MachineTranslationApiClient]] = {
    "DeepL": DeepLApiClient,
    "Google Translate": GoogleTranslateApiClient,
}


def _get_form_classes() -> dict[str, ModelFormMetaclass]:
    # Imported lazily to avoid a circular import: these form modules import
    # `queue_translations` from this module, so importing them at module
    # level here would create an import cycle.
    from ...cms.forms.events.event_translation_form import EventTranslationForm
    from ...cms.forms.pages.page_translation_form import PageTranslationForm
    from ...cms.forms.pois.poi_translation_form import POITranslationForm
    from ...cms.forms.push_notifications.push_notification_translation_form import (
        PushNotificationTranslationForm,
    )

    return {
        "page": PageTranslationForm,
        "event": EventTranslationForm,
        "poi": POITranslationForm,
        "pushnotification": PushNotificationTranslationForm,
    }


_TRANSLATION_FILTER_FIELD: dict[str, str] = {
    "page": "page__in",
    "event": "event__in",
    "poi": "poi__in",
    "pushnotification": "push_notification__in",
}


def get_mt_redis_lock_key(content_type: str, object_id: int, language_slug: str) -> str:
    return f"mt_lock:{content_type}:{object_id}:{language_slug}"


def get_mt_task_ids(
    content_type: str, object_ids: list[int], language_slugs: list[str]
) -> dict[ObjectIdAndLanguageSlug, str | None]:
    """
    Batch-resolve the machine translation task IDs for every (object_id, language_slug)
    pair in one cache round trip. The returned dict contains an entry for every requested
    pair:

    A value of None means no MT task is currently running for that pair, a string value
    is the Celery task id.
    """
    lock_keys = {
        (object_id, language_slug): get_mt_redis_lock_key(
            content_type, object_id, language_slug
        )
        for object_id in object_ids
        for language_slug in language_slugs
    }
    cached = cache.get_many(lock_keys.values())
    return {pair: cached.get(key) for pair, key in lock_keys.items()}


#: How long an unread translation report stays queued for the user, in case
#: they never revisit the relevant list view (safety net, not a hard rule).
_MT_REPORT_TTL = 60 * 60 * 24 * 7  # 7 days

#: Safety net for a hard-killed worker (finally can't run then); longer than
#: CELERY_TASK_TIME_LIMIT so it never expires a still-running task's lock.
_MT_LOCK_TTL = 60 * 60 * 4  # 4 hours


def get_mt_report_cache_key(user_id: int, region_id: int, content_type: str) -> str:
    return f"mt_report:{user_id}:{region_id}:{content_type}"


def _queue_mt_report(
    user_id: int,
    region_id: int,
    content_type: str,
    language_slugs: list[str],
    translation_report: dict[str, dict[str, Any]],
) -> None:
    """
    Append a finished translation report to the list of reports the user has
    not yet seen. Read-modify-write, not atomic - see discussion about
    accepting rare race conditions between concurrently finishing tasks
    for the same user/region/content_type.
    """
    key = get_mt_report_cache_key(user_id, region_id, content_type)
    reports = cache.get(key) or []
    reports.append(
        {
            "language_slugs": language_slugs,
            "results": translation_report,
        }
    )
    cache.set(key, reports, timeout=_MT_REPORT_TTL)


def _get_translation_queryset(
    content_type: str, content_objects: QuerySet[Any], language_slug: str
) -> QuerySet[Any]:
    translation_model = apps.get_model("cms", f"{content_type}translation")
    return translation_model.objects.filter(
        **{_TRANSLATION_FILTER_FIELD[content_type]: content_objects},
        language__slug=language_slug,
    )


def _get_language_report(
    client: MachineTranslationApiClient,
) -> dict[str, str | dict[str, str]]:
    return {
        "succeeded": client.get_successful_translation_message(),
        "refreshed": client.get_refreshed_translations_message(),
        "failed": {
            "too-long": client.get_too_long_text_message(),
            "exceeds-limit": client.get_exceeds_limit_message(),
            "insufficient-hix": client.get_insufficient_hix_score_message(),
            "no-source-translation": client.get_no_source_translation_message(),
            "no-changes-made": client.get_no_changes_made_message(),
            "no-reason": client.get_failed_translation_message(),
        },
    }


def _resolve_user(user_id: int) -> User:
    user = User.objects.filter(id=user_id).first()
    if user is None:
        raise ValueError("User not found")
    return user


def _resolve_region(region_id: int) -> Region:
    region = Region.objects.filter(id=region_id).first()
    if region is None:
        raise ValueError("Region not found")
    return region


def _resolve_form_class(content_type: str) -> ModelFormMetaclass:
    form_class = _get_form_classes().get(content_type)
    if form_class is None:
        raise ValueError("Content type not found")
    return form_class


def _mark_language_failed(
    content_objects: QuerySet[Any], error_message: str
) -> dict[str, dict[str, Any]]:
    return {
        str(content_object.id): {"exception": error_message}
        for content_object in content_objects
    }


def _resolve_client_for_language(
    region: Region,
    language_slug: str,
    mock_request: HttpRequest,
    form_class: ModelFormMetaclass,
    clients_by_provider: dict[str, MachineTranslationApiClient],
) -> tuple[MachineTranslationApiClient | None, str | None]:
    """
    Resolve (and cache) the MT client to use for one language. Returns
    ``(client, None)`` on success, or ``(None, error_message)`` if this
    language can't be translated at all - either because it doesn't exist in
    this region, MT is disabled for it, or its configured provider isn't one
    of the supported ones.
    """
    language_node = region.language_node_by_slug.get(language_slug)
    if language_node is None:
        return None, gettext(
            "The translation into '{language_slug}' cannot be executed, "
            "because this language does not exist in this region."
        ).format(language_slug=language_slug)

    if language_node.mt_provider is None:
        return None, gettext(
            "The translation into '{language_slug}' cannot be executed, "
            "because machine translation is disabled for this language."
        ).format(language_slug=language_slug)

    provider_name = language_node.mt_provider.name
    if client := clients_by_provider.get(provider_name):
        return client, None

    client_class: type[MachineTranslationApiClient] | None = _API_CLIENTS.get(
        provider_name
    )
    if client_class is None:
        return None, gettext("Provider does not exist")

    client = client_class(mock_request, form_class)
    clients_by_provider[provider_name] = client
    return client, None


def _translate_language(
    task: Task,
    client: MachineTranslationApiClient,
    content_objects: QuerySet[Any],
    language_slug: str,
    progress_base: float,
    progress_denominator: int,
) -> dict[str, dict[str, Any]]:
    """
    Translate every content object into one language, reporting per-object
    progress along the way. Returns this language's per-object report
    entries - a mix of successes (:func:`_get_language_report`) and
    per-object failures that don't abort the rest of the batch.
    """
    report: dict[str, dict[str, Any]] = {}
    for i_objects, content_object in enumerate(content_objects):
        current_meta = {
            "current_language": language_slug,
            "progress": progress_base + i_objects / progress_denominator,
        }
        try:
            task.update_state(state="IN_PROGRESS", meta=current_meta)
            client.translate_queryset([content_object], language_slug)
        except Exception as e:
            logger.exception(
                "Machine translation of %r into %r failed for %r",
                content_object,
                language_slug,
                client,
            )
            report[str(content_object.id)] = {"exception": str(e)}
            task.update_state(state="IN_PROGRESS", meta=current_meta)
            continue
        report[str(content_object.id)] = _get_language_report(client)
    return report


def _release_locks(
    content_type: str, object_ids: list[int], language_slugs: list[str]
) -> None:
    # No DB dependency, so this can run unconditionally from `finally`.
    for obj_id in object_ids:
        for language_slug in language_slugs:
            cache.delete(get_mt_redis_lock_key(content_type, obj_id, language_slug))


def _clear_machine_translation_flag(
    content_type: str, object_ids: list[int], language_slugs: list[str]
) -> None:
    # Builds its own queryset (rather than reusing the caller's
    # content_objects) so this can also run from `finally`. May raise
    # LookupError if content_type itself was invalid - callers should
    # expect that.
    content_model = apps.get_model("cms", content_type)
    content_objects = content_model.objects.filter(id__in=object_ids)
    for language_slug in language_slugs:
        _get_translation_queryset(content_type, content_objects, language_slug).update(
            currently_in_machine_translation=False
        )


def _build_pages_data(
    content_objects: QuerySet[Any], language_slugs: list[str]
) -> dict[str, dict[str, Any]]:
    """
    Build the final per-object, per-language payload returned as this
    task's result. `content_objects` are the same instances used throughout
    translation, so their cached translations must be invalidated first -
    otherwise `get_translation()`/`get_translation_state()` would still see
    whatever was cached before this task created or updated them.
    """
    for content_object in content_objects:
        content_object.invalidate_cached_translations()

    return {
        str(content_object.id): {
            language_slug: {
                "translation_state": content_object.get_translation_state(
                    language_slug
                ),
                **(
                    {
                        "title": translation.title,
                        "slug": translation.slug,
                        "status": translation.get_status_display(),
                        "last_updated": translation.last_updated.isoformat(),
                    }
                    if (translation := content_object.get_translation(language_slug))
                    else {}
                ),
            }
            for language_slug in language_slugs
        }
        for content_object in content_objects
    }


@shared_task(bind=True)
def start_async_translation(
    self: Task,
    user_id: int,
    user_language_slug: str,
    region_id: int,
    content_type: str,
    object_ids: list[int],
    language_slugs: list[str],
) -> dict[str, Any]:
    activate_language(user_language_slug)

    try:
        user = _resolve_user(user_id)
        region = _resolve_region(region_id)
        form_class = _resolve_form_class(content_type)

        mock_request = HttpRequest()
        mock_request.user = user
        mock_request.region = region

        content_model = apps.get_model("cms", content_type)
        content_objects = content_model.objects.filter(id__in=object_ids)

        # The `currently_in_machine_translation` flag is set synchronously in
        # `queue_translations()`, before this task is even queued - see the
        # comment there for why.

        translation_report: dict[str, dict[str, Any]] = defaultdict(dict)
        clients_by_provider: dict[str, MachineTranslationApiClient] = {}

        for i_language, language_slug in enumerate(language_slugs):
            progress_base = i_language / len(language_slugs)
            client, error_message = _resolve_client_for_language(
                region, language_slug, mock_request, form_class, clients_by_provider
            )
            if client is None:
                if error_message is None:
                    raise AssertionError(
                        "_resolve_client_for_language returned no client and no error message"
                    )
                translation_report[language_slug] = _mark_language_failed(
                    content_objects, error_message
                )
                self.update_state(
                    state="IN_PROGRESS",
                    meta={"current_language": language_slug, "progress": progress_base},
                )
                continue

            translation_report[language_slug] = _translate_language(
                self,
                client,
                content_objects,
                language_slug,
                progress_base,
                len(language_slugs) * len(content_objects),
            )

        # Must clear before _build_pages_data(), else a newly-created-but-failed
        # translation would still show MACHINE_TRANSLATION_IN_PROGRESS via the lock.
        _release_locks(content_type, object_ids, language_slugs)
        _clear_machine_translation_flag(content_type, object_ids, language_slugs)

        pages_data = _build_pages_data(content_objects, language_slugs)

        _queue_mt_report(
            user_id, region_id, content_type, language_slugs, translation_report
        )
    finally:
        # Idempotent backstop in case the above never ran (e.g. unknown user/region).
        _release_locks(content_type, object_ids, language_slugs)
        with contextlib.suppress(LookupError):
            _clear_machine_translation_flag(content_type, object_ids, language_slugs)

    # Returning this (rather than calling `self.update_state(state="SUCCESS", ...)`)
    # is what actually makes it the task's final result: once this function
    # returns normally, Celery's own completion handling stores the return
    # value as the SUCCESS result, overwriting any state set via
    # `update_state()` beforehand.
    return {"progress": 1.0, "pages": pages_data}


def acquire_locks(
    content_type: str, object_ids: list[int], language_slugs: list[str], task_id: str
) -> list[str] | None:
    acquired: list[str] = []
    for language_slug in language_slugs:
        for object_id in object_ids:
            key = get_mt_redis_lock_key(content_type, object_id, language_slug)
            if not cache.add(key, task_id, timeout=_MT_LOCK_TTL):
                for k in acquired:
                    cache.delete(k)
                return None
            acquired.append(key)
    return acquired


def queue_translations(
    *,
    request: HttpRequest,
    user_id: int,
    region_id: int,
    content_type: str,
    object_ids: list[int],
    language_slugs: list[str],
) -> None:
    # create redis locks
    task_id = str(uuid4())
    acquired_locks = acquire_locks(content_type, object_ids, language_slugs, task_id)

    if acquired_locks is None:
        messages.error(
            request,
            _(
                "The translation could not be started, because at least one of "
                "the requested {content_type} is already being translated into "
                "one of the requested languages."
            ).format(content_type=content_type),
        )
        return

    # Set the flag synchronously, before queueing the task: the task itself
    # only starts running once a worker picks it up, some indeterminate time
    # later, which would otherwise race with the redirect this triggers -
    # the very next render could easily happen before the flag was set.
    content_model = apps.get_model("cms", content_type)
    content_objects = content_model.objects.filter(id__in=object_ids)
    for language_slug in language_slugs:
        _get_translation_queryset(content_type, content_objects, language_slug).update(
            currently_in_machine_translation=True
        )
    user_language_slug = get_language()
    # Deferred until the enclosing transaction commits: dispatching
    # immediately could let a worker read stale (pre-commit) data, or run
    # the task at all even if this transaction later rolls back.
    transaction.on_commit(
        lambda: start_async_translation.apply_async(
            kwargs={
                "user_id": user_id,
                "user_language_slug": user_language_slug,
                "region_id": region_id,
                "content_type": content_type,
                "object_ids": object_ids,
                "language_slugs": language_slugs,
            },
            task_id=task_id,
        )
    )
