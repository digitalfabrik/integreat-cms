from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.cache import cache

from integreat_cms.cms.constants.translation_status import (
    MACHINE_TRANSLATION_IN_PROGRESS,
    MISSING,
)
from integreat_cms.cms.models import Region
from integreat_cms.cms.views.utils.translation_coverage import (
    get_translation_and_word_count,
)
from integreat_cms.core.utils.machine_translation_celery_task import (
    get_mt_redis_lock_key,
    get_mt_task_ids,
)

REGION_SLUG = "augsburg"
PAGE_ID = 2
TARGET_LANGUAGE_SLUG = "en"


@pytest.mark.django_db
def test_translation_and_word_count_batches_the_mt_lock_lookup(
    load_test_data: None,
) -> None:
    """
    Regression test for the switch to a batched ``get_mt_task_ids()`` lookup:
    previously each (page, language) pair without an existing translation
    resolved its machine translation lock with its own `cache.get()` call,
    instead of one `get_mt_task_ids()` call up front. Spying on
    `get_mt_task_ids` (rather than only asserting the end result) is what
    actually catches a regression here - the per-object fallback path would
    produce the same correct result, just with many more cache round trips.
    """
    region = Region.objects.get(slug=REGION_SLUG)
    language = next(
        lang for lang in region.active_languages if lang.slug == TARGET_LANGUAGE_SLUG
    )

    lock_key = get_mt_redis_lock_key("page", PAGE_ID, TARGET_LANGUAGE_SLUG)
    cache.add(lock_key, "some-task-id", timeout=None)
    try:
        with patch(
            "integreat_cms.cms.views.utils.translation_coverage.get_mt_task_ids",
            wraps=get_mt_task_ids,
        ) as spy_get_mt_task_ids:
            translation_count, _word_count = get_translation_and_word_count(region)
    finally:
        cache.delete(lock_key)

    spy_get_mt_task_ids.assert_called_once()
    assert translation_count[language][MACHINE_TRANSLATION_IN_PROGRESS] >= 1


@pytest.mark.django_db
def test_translation_and_word_count_reports_missing_without_a_lock(
    load_test_data: None,
) -> None:
    region = Region.objects.get(slug=REGION_SLUG)
    language = next(
        lang for lang in region.active_languages if lang.slug == TARGET_LANGUAGE_SLUG
    )

    translation_count, _word_count = get_translation_and_word_count(region)

    assert translation_count[language][MISSING] >= 1
