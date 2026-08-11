from __future__ import annotations

import json

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Language, Page, PageTranslation, Region
from integreat_cms.cms.views.utils.content_edit_lock import (
    _get_active_child_mt_task_id,
    _get_machine_translation_status,
)
from integreat_cms.core.utils.machine_translation_celery_task import (
    get_mt_redis_lock_key,
)

REGION_SLUG = "augsburg"
#: augsburg's root language - "en" and "de-si" are both its direct children
SOURCE_LANGUAGE_SLUG = "de"
CHILD_LANGUAGE_SLUG = "en"
#: A direct child of "de" that is deliberately left out of
#: `supported_target_languages` below, so its `mt_provider` resolves to
#: `None` while a lock for it can still exist.
UNSUPPORTED_CHILD_LANGUAGE_SLUG = "de-si"


@pytest.fixture(autouse=True)
def _mt_provider_supported_languages() -> None:
    # Mirrors the pattern in tests/core/utils/test_machine_translation_celery_task.py
    apps.get_app_config("deepl_api").supported_source_languages = ["de", "en"]
    apps.get_app_config("deepl_api").supported_target_languages = [CHILD_LANGUAGE_SLUG]
    apps.get_app_config("google_translate_api").supported_source_languages = [
        "de",
        "en",
    ]
    apps.get_app_config("google_translate_api").supported_target_languages = [
        CHILD_LANGUAGE_SLUG
    ]


@pytest.fixture()
def page(load_test_data: None) -> Page:
    region = Region.objects.get(slug=REGION_SLUG)
    new_page = Page.add_root(region=region)
    new_page.save()
    PageTranslation.objects.create(
        page=new_page,
        language=Language.objects.get(slug=SOURCE_LANGUAGE_SLUG),
        title="Source title",
        slug="source-title",
        content="",
        status=status.PUBLIC,
    )
    return new_page


# --- _get_active_child_mt_task_id ---


@pytest.mark.django_db
def test_active_child_mt_task_id_none_for_root_language(page: Page) -> None:
    # "de" is augsburg's root language - it has no parent, so it is never
    # itself a *child* language, and this function only ever looks at a
    # language's children, not the language itself.
    assert _get_active_child_mt_task_id(page, SOURCE_LANGUAGE_SLUG) is None


@pytest.mark.django_db
def test_active_child_mt_task_id_none_without_any_lock(page: Page) -> None:
    assert _get_active_child_mt_task_id(page, SOURCE_LANGUAGE_SLUG) is None


@pytest.mark.django_db
def test_active_child_mt_task_id_found_for_locked_child(page: Page) -> None:
    lock_key = get_mt_redis_lock_key("page", page.id, CHILD_LANGUAGE_SLUG)
    cache.set(lock_key, "task-123", timeout=None)

    assert _get_active_child_mt_task_id(page, SOURCE_LANGUAGE_SLUG) == "task-123"


@pytest.mark.django_db
def test_active_child_mt_task_id_found_even_without_provider_support(
    page: Page,
) -> None:
    # "de-si" is a direct child of "de" but is deliberately excluded from
    # supported_target_languages above, so `mt_provider` is None for it -
    # the lock's existence alone must still be enough to find it (see the
    # docstring on `_get_active_child_mt_task_id` for why this is correct).
    lock_key = get_mt_redis_lock_key("page", page.id, UNSUPPORTED_CHILD_LANGUAGE_SLUG)
    cache.set(lock_key, "task-456", timeout=None)

    assert _get_active_child_mt_task_id(page, SOURCE_LANGUAGE_SLUG) == "task-456"


# --- _get_machine_translation_status ---


@pytest.mark.django_db
def test_machine_translation_status_default_for_unsupported_type(page: Page) -> None:
    assert _get_machine_translation_status(
        page.id, "ImprintPage", CHILD_LANGUAGE_SLUG
    ) == {
        "currentlyInMachineTranslation": False,
        "activeChildTranslationTaskId": None,
    }


@pytest.mark.django_db
def test_machine_translation_status_default_without_language_slug(page: Page) -> None:
    assert _get_machine_translation_status(page.id, "Page", None) == {
        "currentlyInMachineTranslation": False,
        "activeChildTranslationTaskId": None,
    }


@pytest.mark.django_db
def test_machine_translation_status_default_for_nonexistent_object() -> None:
    assert _get_machine_translation_status(999999, "Page", CHILD_LANGUAGE_SLUG) == {
        "currentlyInMachineTranslation": False,
        "activeChildTranslationTaskId": None,
    }


@pytest.mark.django_db
def test_machine_translation_status_reports_target_flag_independently(
    page: Page,
) -> None:
    PageTranslation.objects.create(
        page=page,
        language=Language.objects.get(slug=CHILD_LANGUAGE_SLUG),
        title="Target title",
        slug="target-title",
        content="",
        currently_in_machine_translation=True,
    )

    result = _get_machine_translation_status(page.id, "Page", CHILD_LANGUAGE_SLUG)

    assert result["currentlyInMachineTranslation"] is True
    # No child task is running - this is a target-language check, not a
    # source-language one, so the two facts are independent of each other.
    assert result["activeChildTranslationTaskId"] is None


@pytest.mark.django_db
def test_machine_translation_status_reports_source_task_independently(
    page: Page,
) -> None:
    lock_key = get_mt_redis_lock_key("page", page.id, CHILD_LANGUAGE_SLUG)
    cache.set(lock_key, "task-789", timeout=None)

    result = _get_machine_translation_status(page.id, "Page", SOURCE_LANGUAGE_SLUG)

    assert result["currentlyInMachineTranslation"] is False
    assert result["activeChildTranslationTaskId"] == "task-789"


# --- content_edit_lock_heartbeat (view) ---


@pytest.mark.django_db
def test_heartbeat_includes_machine_translation_status(page: Page) -> None:
    lock_key = get_mt_redis_lock_key("page", page.id, CHILD_LANGUAGE_SLUG)
    cache.set(lock_key, "task-abc", timeout=None)

    client = Client()
    client.force_login(get_user_model().objects.get(username="root"))
    url = reverse("content_edit_lock_heartbeat", kwargs={"region_slug": REGION_SLUG})

    response = client.post(
        url,
        data=json.dumps(
            {
                "key": json.dumps([page.id, "Page"]),
                "force": False,
                "languageSlug": SOURCE_LANGUAGE_SLUG,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["currentlyInMachineTranslation"] is False
    assert data["activeChildTranslationTaskId"] == "task-abc"
