from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.core.cache import cache
from django.urls import reverse

from integreat_cms.cms.constants.translation_status import (
    CHART_CHOICES,
    MACHINE_TRANSLATION_IN_PROGRESS,
)
from integreat_cms.cms.models import Region
from integreat_cms.core.utils.machine_translation_celery_task import (
    get_mt_redis_lock_key,
)

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"
PAGE_ID = 2
TARGET_LANGUAGE_SLUG = "en"


@pytest.mark.django_db
def test_translation_coverage_chart_includes_machine_translation_in_progress(
    load_test_data: None,
    admin_client: Client,
) -> None:
    """
    Regression test: `MACHINE_TRANSLATION_IN_PROGRESS` used to be counted by
    `get_translation_and_word_count()` but never rendered, because the chart
    built one dataset per `CHOICES` member and that status wasn't one of them
    - so a page currently being machine-translated silently vanished from
    the chart instead of showing up under its own bar segment.
    """
    region = Region.objects.get(slug=REGION_SLUG)
    language = next(
        lang for lang in region.active_languages if lang.slug == TARGET_LANGUAGE_SLUG
    )

    lock_key = get_mt_redis_lock_key("page", PAGE_ID, TARGET_LANGUAGE_SLUG)
    cache.add(lock_key, "some-task-id", timeout=None)
    try:
        url = reverse("translation_coverage", kwargs={"region_slug": REGION_SLUG})
        response = admin_client.get(url)
    finally:
        cache.delete(lock_key)

    assert response.status_code == 200
    chart_data = response.context["chart_data"]

    language_index = chart_data["labels"].index(language.translated_name)
    in_progress_dataset = next(
        dataset
        for dataset, (status, _label) in zip(
            chart_data["datasets"], CHART_CHOICES, strict=True
        )
        if status == MACHINE_TRANSLATION_IN_PROGRESS
    )
    assert in_progress_dataset["data"][language_index] >= 1
