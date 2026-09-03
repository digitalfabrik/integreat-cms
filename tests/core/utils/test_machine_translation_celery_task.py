from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from celery import Task
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import RequestFactory

from integreat_cms.cms.models import (
    Language,
    LanguageTreeNode,
    Page,
    PageTranslation,
    Region,
)
from integreat_cms.core.utils.machine_translation_api_client import (
    MachineTranslationApiClient,
)
from integreat_cms.core.utils.machine_translation_celery_task import (
    get_mt_redis_lock_key,
    queue_translations,
    start_async_translation,
)

if TYPE_CHECKING:
    from typing import Any
    from unittest.mock import MagicMock

REGION_SLUG = "augsburg"
PAGE_ID = 28
CONTROL_PAGE_ID = 1
TARGET_LANGUAGE_SLUG = "en"


@pytest.fixture(autouse=True)
def _mt_provider_supported_languages() -> None:
    # `ready()` on the DeepL/Google Translate AppConfigs only populates these
    # by making a real API call, and only when running under `runserver`, Apache,
    # or a real Celery worker (see deepl_api/apps.py, google_translate_api/apps.py).
    # None of that applies under pytest, so `LanguageTreeNode.mt_provider` would
    # otherwise resolve to None for every language. Mirrors the pattern used in
    # tests/mt_api/deepl_api_test.py and tests/mt_api/google_translate_api_test.py.
    apps.get_app_config("deepl_api").supported_source_languages = ["de", "en"]
    apps.get_app_config("deepl_api").supported_target_languages = ["en", "fa"]
    apps.get_app_config("google_translate_api").supported_source_languages = [
        "de",
        "en",
    ]
    apps.get_app_config("google_translate_api").supported_target_languages = [
        "en",
        "fa",
    ]


@pytest.fixture()
def task_kwargs(load_test_data: None) -> dict[str, Any]:
    return {
        "user_id": get_user_model().objects.get(username="root").id,
        "user_language_slug": "en",
        "region_id": Region.objects.get(slug=REGION_SLUG).id,
        "content_type": "page",
        "object_ids": [PAGE_ID],
        "language_slugs": [TARGET_LANGUAGE_SLUG],
    }


@pytest.fixture()
def update_state_calls() -> Any:
    with patch.object(Task, "update_state") as mock_update_state:
        yield mock_update_state


@pytest.fixture()
def stub_translate_queryset() -> Any:
    with patch.object(MachineTranslationApiClient, "translate_queryset") as mock:
        yield mock


@pytest.fixture()
def stub_language_report() -> Any:
    with patch(
        "integreat_cms.core.utils.machine_translation_celery_task._get_language_report",
        return_value={"succeeded": "ok", "failed": {}},
    ) as mock:
        yield mock


@pytest.fixture()
def spy_queue_mt_report() -> Any:
    with patch(
        "integreat_cms.core.utils.machine_translation_celery_task._queue_mt_report"
    ) as mock:
        yield mock


class _UnsupportedProvider:
    """A stand-in for a provider that is configured on a language but has no
    entry in API_CLIENTS (e.g. SummAI, which is being phased out)."""

    name = "SummAI"


@pytest.fixture()
def stub_unsupported_mt_provider() -> Any:
    # `mt_provider` is a `cached_property` on LanguageTreeNode; patching the
    # class attribute with a plain object bypasses the descriptor entirely,
    # so every language node resolves to this fake, unsupported provider.
    with patch.object(LanguageTreeNode, "mt_provider", _UnsupportedProvider()):
        yield


@pytest.mark.django_db
def test_unknown_user_id_reports_failure(task_kwargs: dict[str, Any]) -> None:
    task_kwargs["user_id"] = 999999
    translation = PageTranslation.objects.get(
        page_id=PAGE_ID, language__slug=TARGET_LANGUAGE_SLUG
    )

    result = start_async_translation.apply(kwargs=task_kwargs, throw=False)

    assert result.state == "FAILURE"
    assert str(result.result) == "User not found"
    translation.refresh_from_db()
    assert translation.currently_in_machine_translation is False


@pytest.mark.django_db
def test_lock_released_after_validation_failure(task_kwargs: dict[str, Any]) -> None:
    task_kwargs["user_id"] = 999999
    lock_key = get_mt_redis_lock_key(
        task_kwargs["content_type"], PAGE_ID, TARGET_LANGUAGE_SLUG
    )
    cache.add(lock_key, "some-task-id", timeout=None)

    start_async_translation.apply(kwargs=task_kwargs, throw=False)

    assert cache.get(lock_key) is None


@pytest.mark.django_db
def test_unknown_region_id_reports_failure(task_kwargs: dict[str, Any]) -> None:
    task_kwargs["region_id"] = 999999

    result = start_async_translation.apply(kwargs=task_kwargs, throw=False)

    assert result.state == "FAILURE"
    assert str(result.result) == "Region not found"


@pytest.mark.django_db
def test_unknown_content_type_reports_failure(task_kwargs: dict[str, Any]) -> None:
    task_kwargs["content_type"] = "not-a-real-type"

    result = start_async_translation.apply(kwargs=task_kwargs, throw=False)

    assert result.state == "FAILURE"
    assert str(result.result) == "Content type not found"


@pytest.mark.django_db
def test_unsupported_provider_skips_language_without_aborting(
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_unsupported_mt_provider: None,
    spy_queue_mt_report: MagicMock,
) -> None:
    # Unlike an unknown user/region/content type (which abort the whole task),
    # a language whose configured provider isn't supported is skipped for
    # that language only - the task still completes successfully overall, see
    # test_one_language_failure_does_not_abort_others below.
    result = start_async_translation.apply(kwargs=task_kwargs)

    assert result.state == "SUCCESS"
    spy_queue_mt_report.assert_called_once_with(
        task_kwargs["user_id"],
        task_kwargs["region_id"],
        task_kwargs["content_type"],
        task_kwargs["language_slugs"],
        {
            TARGET_LANGUAGE_SLUG: {
                str(PAGE_ID): {"exception": "Provider does not exist"}
            }
        },
    )


@pytest.mark.django_db
def test_empty_object_ids_and_language_slugs_completes(
    task_kwargs: dict[str, Any],
    spy_queue_mt_report: MagicMock,
) -> None:
    task_kwargs["object_ids"] = []
    task_kwargs["language_slugs"] = []

    result = start_async_translation.apply(kwargs=task_kwargs)

    assert result.state == "SUCCESS"
    assert result.result == {"progress": 1.0, "pages": {}}
    spy_queue_mt_report.assert_called_once_with(
        task_kwargs["user_id"],
        task_kwargs["region_id"],
        task_kwargs["content_type"],
        [],
        {},
    )


@pytest.mark.django_db
def test_flag_set_during_translation_and_cleared_after(
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_translate_queryset: MagicMock,
    stub_language_report: MagicMock,
) -> None:
    """
    The `currently_in_machine_translation` flag is set synchronously in
    `queue_translations()`, before the task is even queued (see the
    render-time race condition this was fixed for) - `start_async_translation`
    itself no longer sets it at all. So this has to go through
    `queue_translations()`, not call the task directly, to exercise the
    actual flag-setting path - calling the task directly (as this test used
    to) means the flag is never set, regardless of anything else.
    """
    flag_during_call = {}

    def fake_translate(queryset: Any, language_slug: str) -> None:
        translation = PageTranslation.objects.get(
            page_id=PAGE_ID, language__slug=TARGET_LANGUAGE_SLUG
        )
        flag_during_call["value"] = translation.currently_in_machine_translation

    stub_translate_queryset.side_effect = fake_translate

    # `CELERY_TASK_ALWAYS_EAGER` (autouse, see conftest.py) makes the queued
    # task run synchronously as part of this call, so by the time it
    # returns, the whole lock-acquire -> translate -> flag-clear cycle has
    # already happened.
    queue_translations(
        request=RequestFactory().get("/"),
        user_id=task_kwargs["user_id"],
        region_id=task_kwargs["region_id"],
        content_type=task_kwargs["content_type"],
        object_ids=task_kwargs["object_ids"],
        language_slugs=task_kwargs["language_slugs"],
    )

    assert flag_during_call["value"] is True
    translation = PageTranslation.objects.get(
        page_id=PAGE_ID, language__slug=TARGET_LANGUAGE_SLUG
    )
    assert translation.currently_in_machine_translation is False


@pytest.mark.django_db
def test_flag_cleared_after_exception(
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_translate_queryset: MagicMock,
) -> None:
    stub_translate_queryset.side_effect = RuntimeError("provider exploded")

    start_async_translation.apply(kwargs=task_kwargs)

    translation = PageTranslation.objects.get(
        page_id=PAGE_ID, language__slug=TARGET_LANGUAGE_SLUG
    )
    assert translation.currently_in_machine_translation is False


@pytest.mark.django_db
def test_flag_scoped_to_requested_objects_only(
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_translate_queryset: MagicMock,
    stub_language_report: MagicMock,
) -> None:
    flag_during_call = {}

    def fake_translate(queryset: Any, language_slug: str) -> None:
        control = PageTranslation.objects.get(
            page_id=CONTROL_PAGE_ID, language__slug=TARGET_LANGUAGE_SLUG
        )
        flag_during_call["value"] = control.currently_in_machine_translation

    stub_translate_queryset.side_effect = fake_translate

    start_async_translation.apply(kwargs=task_kwargs)

    assert flag_during_call["value"] is False
    control = PageTranslation.objects.get(
        page_id=CONTROL_PAGE_ID, language__slug=TARGET_LANGUAGE_SLUG
    )
    assert control.currently_in_machine_translation is False


@pytest.mark.django_db
def test_one_language_failure_does_not_abort_others(
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_translate_queryset: MagicMock,
    stub_language_report: MagicMock,
    spy_queue_mt_report: MagicMock,
) -> None:
    task_kwargs["language_slugs"] = ["en", "fa"]

    def fake_translate(queryset: Any, language_slug: str) -> None:
        if language_slug == "fa":
            raise RuntimeError("provider exploded")

    stub_translate_queryset.side_effect = fake_translate

    result = start_async_translation.apply(kwargs=task_kwargs)

    assert result.state == "SUCCESS"
    assert result.result["progress"] == 1.0

    spy_queue_mt_report.assert_called_once_with(
        task_kwargs["user_id"],
        task_kwargs["region_id"],
        task_kwargs["content_type"],
        ["en", "fa"],
        {
            "fa": {"28": {"exception": "provider exploded"}},
            "en": {"28": {"succeeded": "ok", "failed": {}}},
        },
    )


@pytest.mark.django_db
def test_progress_reported_per_language(
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_translate_queryset: MagicMock,
    stub_language_report: MagicMock,
    spy_queue_mt_report: MagicMock,
) -> None:
    task_kwargs["language_slugs"] = ["en", "fa"]

    result = start_async_translation.apply(kwargs=task_kwargs)

    progress_calls = [
        c.kwargs
        for c in update_state_calls.call_args_list
        if c.kwargs.get("state") == "IN_PROGRESS"
    ]
    assert [c["meta"]["current_language"] for c in progress_calls] == ["en", "fa"]
    assert [c["meta"]["progress"] for c in progress_calls] == [0.0, 0.5]

    assert result.state == "SUCCESS"
    assert result.result["progress"] == 1.0

    report = spy_queue_mt_report.call_args.args[-1]
    assert set(report) == {"en", "fa"}
    assert set(report["en"]) == {"28"}


@pytest.mark.django_db
def test_cache_lock_keys_deleted_for_every_object_and_language(
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_translate_queryset: MagicMock,
    stub_language_report: MagicMock,
) -> None:
    task_kwargs["language_slugs"] = ["en", "fa"]

    with patch(
        "integreat_cms.core.utils.machine_translation_celery_task.cache"
    ) as mock_cache:
        start_async_translation.apply(kwargs=task_kwargs)

    mock_cache.delete.assert_any_call(f"mt_lock:page:{PAGE_ID}:en")
    mock_cache.delete.assert_any_call(f"mt_lock:page:{PAGE_ID}:fa")
    # Released twice on the success path: once explicitly, once more via the
    # finally-block backstop.
    assert mock_cache.delete.call_count == 4


@pytest.mark.django_db
@pytest.mark.parametrize("content_type", ["page", "event", "poi", "pushnotification"])
def test_content_type_resolves_form_and_translation_model(
    content_type: str,
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_translate_queryset: MagicMock,
    stub_language_report: MagicMock,
) -> None:
    task_kwargs["content_type"] = content_type
    task_kwargs["object_ids"] = []

    result = start_async_translation.apply(kwargs=task_kwargs)

    assert result.state == "SUCCESS"


@pytest.mark.django_db
def test_pages_data_reflects_freshly_created_translation(
    task_kwargs: dict[str, Any],
    update_state_calls: MagicMock,
    stub_translate_queryset: MagicMock,
    stub_language_report: MagicMock,
    spy_queue_mt_report: MagicMock,
) -> None:
    """
    Regression test for a real bug found via manual testing: `pages_data`
    used to report "MISSING" for a translation that had just been created
    by this very task, because `get_translation()` reads from a
    `@cached_property` that had already been populated (as "does not exist")
    before the translation was created, and nothing invalidated it
    afterward. Fixed by calling `invalidate_cached_translations()` on every
    `content_object` right before building `pages_data`.

    Unlike the other tests in this module, `stub_translate_queryset`'s
    `side_effect` here actually creates a real `PageTranslation` row - the
    previous tests all leave it a no-op, which is exactly why this gap
    existed without any test catching it.
    """
    region = Region.objects.get(slug=REGION_SLUG)
    language = Language.objects.get(slug=TARGET_LANGUAGE_SLUG)
    page = Page.add_root(region=region)
    page.save()

    def fake_translate(queryset: Any, language_slug: str) -> None:
        for content_object in queryset:
            PageTranslation.objects.create(
                page=content_object,
                language=language,
                title="Translated title",
                slug="translated-title",
                content="",
            )

    stub_translate_queryset.side_effect = fake_translate
    task_kwargs["object_ids"] = [page.id]

    result = start_async_translation.apply(kwargs=task_kwargs)

    assert result.state == "SUCCESS"
    page_data = result.result["pages"][str(page.id)][TARGET_LANGUAGE_SLUG]
    assert page_data["translation_state"] != "MISSING"
    assert page_data["title"] == "Translated title"
    assert page_data["slug"] == "translated-title"
