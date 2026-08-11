from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from celery import shared_task, Task
from django.apps import apps
from django.contrib import messages
from django.core.cache import cache
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

    from .machine_translation_api_client import MachineTranslationApiClient

logger = logging.getLogger(__name__)

API_CLIENTS: dict[str, type[MachineTranslationApiClient]] = {
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


TRANSLATION_FILTER_FIELD: dict[str, str] = {
    "page": "page__in",
    "event": "event__in",
    "poi": "poi__in",
    "pushnotification": "push_notification__in",
}


def get_mt_redis_lock_key(content_type: str, object_id: int, language_slug: str) -> str:
    return f"mt_lock:{content_type}:{object_id}:{language_slug}"


def get_mt_task_ids(
    content_type: str, object_ids: list[int], language_slugs: list[str]
) -> dict[tuple[int, str], str | None]:
    """
    Batch-resolve the machine translation task id (if any) for every
    (object_id, language_slug) pair in one cache round trip, instead of
    checking each lock individually - for callers that need this for many
    objects at once (e.g. a whole list view render).
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
MT_REPORT_TTL = 60 * 60 * 24 * 7  # 7 days


def get_mt_report_cache_key(user_id: int, region_id: int, content_type: str) -> str:
    return f"mt_report:{user_id}:{region_id}:{content_type}"


def queue_mt_report(
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
    cache.set(key, reports, timeout=MT_REPORT_TTL)


def get_translation_queryset(
    content_type: str, content_objects: QuerySet[Any], language_slug: str
) -> QuerySet[Any]:
    translation_model = apps.get_model("cms", f"{content_type}translation")
    return translation_model.objects.filter(
        **{TRANSLATION_FILTER_FIELD[content_type]: content_objects},
        language__slug=language_slug,
    )


def get_language_report(
    client: MachineTranslationApiClient,
) -> dict[str, str | dict[str, str]]:
    return {
        "succeeded": client.get_successful_translation_message(lazy=False),
        "failed": {
            "too-long": client.get_too_long_text_message(lazy=False),
            "exceeds-limit": client.get_exceeds_limit_message(lazy=False),
            "insufficient-hix": client.get_insufficient_hix_score_message(lazy=False),
            "no-source-translation": client.get_no_source_translation_message(
                lazy=False
            ),
            "no-changes-made": client.get_no_changes_made_message(lazy=False),
            "no-reason": client.get_failed_translation_message(lazy=False),
        },
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
    current_state = None
    current_meta: dict[str, Any] = {}
    translation_report: dict[str, dict[str, Any]] = defaultdict(dict)
    clients_by_provider: dict[str, MachineTranslationApiClient] = {}

    activate_language(user_language_slug)

    user = User.objects.filter(id=user_id).first()
    if user is None:
        raise ValueError(gettext("User not found"))

    region = Region.objects.filter(id=region_id).first()
    if region is None:
        raise ValueError(gettext("Region not found"))

    mock_request = HttpRequest()
    mock_request.user = user
    mock_request.region = region

    form_class = _get_form_classes().get(content_type)
    if form_class is None:
        raise ValueError(gettext("Content type not found"))

    content_model = apps.get_model("cms", content_type)

    content_objects = content_model.objects.filter(id__in=object_ids)

    # The `currently_in_machine_translation` flag is set synchronously in
    # `queue_translations()`, before this task is even queued - see the
    # comment there for why.

    current_meta = {"progress": 0, "results": defaultdict(dict)}
    current_state = "IN_PROGRESS"

    for i_language, language_slug in enumerate(language_slugs):
        language_node = region.language_node_by_slug.get(language_slug)
        if language_node is None:
            error_message = gettext(
                "The translation into '{language_slug}' cannot be executed, "
                "because this language does not exist in this region."
            ).format(language_slug=language_slug)
            for content_object in content_objects:
                translation_report[language_slug][str(content_object.id)] = {
                    "exception": error_message
                }
            self.update_state(
                state=current_state,
                meta={
                    "current_language": language_slug,
                    "progress": i_language / len(language_slugs),
                    "error": error_message,
                },
            )
            continue

        if language_node.mt_provider is None:
            error_message = gettext(
                "The translation into '{language_slug}' cannot be executed, "
                "because machine translation is disabled for this language."
            ).format(language_slug=language_slug)
            for content_object in content_objects:
                translation_report[language_slug][str(content_object.id)] = {
                    "exception": error_message
                }
            self.update_state(
                state=current_state,
                meta={
                    "current_language": language_slug,
                    "progress": i_language / len(language_slugs),
                    "error": error_message,
                },
            )
            continue
        provider_name = language_node.mt_provider.name

        # get client per provider and cache it
        if not (client := clients_by_provider.get(provider_name)):
            client_class: type[MachineTranslationApiClient] | None = API_CLIENTS.get(
                provider_name
            )
            if client_class is None:
                error_message = gettext("Provider does not exist")
                for content_object in content_objects:
                    translation_report[language_slug][str(content_object.id)] = {
                        "exception": error_message
                    }
                self.update_state(
                    state=current_state,
                    meta={
                        "current_language": language_slug,
                        "progress": i_language / len(language_slugs),
                        "error": error_message,
                    },
                )
                continue
            client = client_class(mock_request, form_class)
            clients_by_provider[provider_name] = client

        # the translation loop
        for i_objects, content_object in enumerate(content_objects):
            try:
                current_meta = {
                    "current_language": language_slug,
                    "progress": i_language / len(language_slugs)
                    + i_objects / (len(language_slugs) * len(content_objects)),
                }
                self.update_state(state=current_state, meta=current_meta)
                client.translate_queryset([content_object], language_slug)
            except Exception as e:
                logger.exception(
                    "Machine translation of %r into %r failed for %r",
                    content_object,
                    language_slug,
                    client,
                )
                translation_report[language_slug][str(content_object.id)] = {
                    "exception": str(e)
                }
                self.update_state(state=current_state, meta=current_meta)
                continue
            translation_report[language_slug][str(content_object.id)] = (
                get_language_report(client)
            )
    for language_slug in language_slugs:
        get_translation_queryset(content_type, content_objects, language_slug).update(
            currently_in_machine_translation=False
        )

    # Delete the locks before computing the final page data below: for an
    # object whose translation was newly *created* but failed, there is still
    # no translation row, so `get_translation_state()` would otherwise fall
    # back to checking the (still-present) lock and incorrectly report
    # MACHINE_TRANSLATION_IN_PROGRESS instead of the real final state.
    for obj_id in object_ids:
        for language_slug in language_slugs:
            cache.delete(get_mt_redis_lock_key(content_type, obj_id, language_slug))

    # `content_objects` are the same instances used throughout the loop
    # above, so `get_translation()`/`get_translation_state()` would
    # otherwise still see whatever was cached before this task created or
    # updated their translations, not the fresh result.
    for content_object in content_objects:
        content_object.invalidate_cached_translations()

    pages_data = {
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

    queue_mt_report(
        user_id, region_id, content_type, language_slugs, translation_report
    )

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
            if not cache.add(key, task_id, timeout=None):
                for k in acquired:
                    cache.delete(k)
                return None
            acquired.append(key)
    return acquired


def queue_translations(
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
        get_translation_queryset(content_type, content_objects, language_slug).update(
            currently_in_machine_translation=True
        )

    user_language_slug = get_language()
    # queue start_async_translations
    start_async_translation.apply_async(
        args=[
            user_id,
            user_language_slug,
            region_id,
            content_type,
            object_ids,
            language_slugs,
        ],
        task_id=task_id,
    )
