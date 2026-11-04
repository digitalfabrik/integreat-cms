from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from integreat_cms.cms.models import (
    MachineTranslationReport,
    PageTranslation,
    Region,
)
from integreat_cms.core.utils.machine_translation_celery_task import (
    get_mt_redis_lock_key,
)

from ..utils import get_command_output

if TYPE_CHECKING:
    from pytest_django.fixtures import Settings

REGION_SLUG = "augsburg"
STALE_PAGE_ID = 28
LOCKED_PAGE_ID = 1
LANGUAGE_SLUG = "en"


@pytest.fixture(autouse=True)
def _redis_cache(settings: Settings) -> None:
    # The test cache is a local memory cache, which is shared with the command since it runs in the same process
    settings.REDIS_CACHE = True


def create_report(task_id: str, age: timedelta) -> MachineTranslationReport:
    """
    Create a machine translation report with the given age

    :param task_id: The id of the task the report belongs to
    :param age: How long ago the report was created
    :return: The created report
    """
    report = MachineTranslationReport.objects.create(
        task_id=task_id,
        user=get_user_model().objects.get(username="root"),
        region=Region.objects.get(slug=REGION_SLUG),
        content_type="page",
        language_slugs=[LANGUAGE_SLUG],
        results={},
    )
    # created_at is set automatically on creation, so it has to be overwritten afterwards
    MachineTranslationReport.objects.filter(id=report.id).update(
        created_at=timezone.now() - age,
    )
    return report


@pytest.mark.django_db
def test_clears_only_flags_without_lock(load_test_data: None) -> None:
    """
    Ensure that only flags whose machine translation lock does not exist anymore are cleared
    """
    PageTranslation.objects.filter(
        page_id__in=[STALE_PAGE_ID, LOCKED_PAGE_ID],
        language__slug=LANGUAGE_SLUG,
    ).update(currently_in_machine_translation=True)
    cache.set(
        get_mt_redis_lock_key("page", LOCKED_PAGE_ID, LANGUAGE_SLUG),
        "running-task-id",
    )

    out, _err = get_command_output("cleanup_machine_translation_flags_and_reports")

    assert (
        "✔ Cleared 1 stale machine translation flag(s) and deleted 0 expired machine translation report(s)."
        in out
    )
    assert not PageTranslation.objects.filter(
        page_id=STALE_PAGE_ID,
        language__slug=LANGUAGE_SLUG,
        currently_in_machine_translation=True,
    ).exists(), "The flag without lock should have been cleared."
    assert PageTranslation.objects.filter(
        page_id=LOCKED_PAGE_ID,
        language__slug=LANGUAGE_SLUG,
        currently_in_machine_translation=True,
    ).exists(), "The flag with lock should remain set."


@pytest.mark.django_db
def test_deletes_only_expired_reports(load_test_data: None) -> None:
    """
    Ensure that only reports older than 30 days are deleted
    """
    expired_report = create_report("expired-task-id", timedelta(days=31))
    recent_report = create_report("recent-task-id", timedelta(days=29))

    out, _err = get_command_output("cleanup_machine_translation_flags_and_reports")

    assert (
        "✔ Cleared 0 stale machine translation flag(s) and deleted 1 expired machine translation report(s)."
        in out
    )
    assert not MachineTranslationReport.objects.filter(id=expired_report.id).exists()
    assert MachineTranslationReport.objects.filter(id=recent_report.id).exists()
