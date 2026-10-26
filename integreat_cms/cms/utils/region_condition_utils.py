"""
This module contains utilities to precompute the condition of regions

The metrics are the same as in the region condition export, but computing them runs heavy queries
over all pages of a region. They are therefore computed once per night and stored in
:class:`~integreat_cms.cms.models.regions.region_condition.RegionCondition`.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from django.db.models import Q
from django.test import override_settings
from django.utils import timezone

from ..constants import region_status
from ..models import Region, RegionCondition

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Final

logger = logging.getLogger(__name__)

#: The metrics which are stored per region, named like the fields of the region condition model
METRICS: Final[list[str]] = [
    "num_broken_links",
    "num_low_hix_pages",
    "num_pages",
    "num_pages_with_missing_or_outdated_translation",
    "num_outdated_pages",
    "num_languages_besides_root_language",
]


@contextmanager
def cacheops_disabled() -> Iterator[None]:
    """
    Disable the cacheops query cache for the duration of the block

    The metrics run large querysets over all pages of a region. Caching them is useless — every
    region is computed only once — and harmful: cacheops stores results of up to several MB per
    key, and doing that for all regions at once grew Redis on production until it was OOM-killed.
    cacheops reads the setting on every query, so overriding it at runtime takes effect immediately.

    :return: A context in which queries bypass the cache
    """
    with override_settings(CACHEOPS_ENABLED=False):
        yield


def compute_region_condition(region: Region) -> dict[str, int]:
    """
    Compute the condition metrics of a region

    The computation is shared with the region condition export, so both always report the same
    numbers.

    :param region: The region whose condition should be computed
    :return: The metrics of the region, keyed like the fields of the region condition model
    """
    # Imported here because the views import the models, which would make a module-level import
    # circular
    from ..views.region_condition.region_condition_actions import (
        RegionConditionResource,
    )

    return {
        metric: getattr(RegionConditionResource, f"dehydrate_{metric}")(region)
        for metric in METRICS
    }


def update_region_conditions() -> tuple[int, int]:
    """
    Compute and store the condition of all active and hidden regions

    A failure in one region is logged and does not stop the others, so a single broken region
    cannot leave all other regions with stale numbers.

    :return: The number of updated and of failed regions
    """
    regions = Region.objects.filter(
        Q(status=region_status.ACTIVE) | Q(status=region_status.HIDDEN),
    ).order_by("slug")
    updated = failed = 0
    with cacheops_disabled():
        for region in regions:
            try:
                metrics = compute_region_condition(region)
            except Exception:
                logger.exception("Could not compute the condition of %r", region)
                failed += 1
                continue
            RegionCondition.objects.update_or_create(
                region=region,
                defaults={**metrics, "computed_at": timezone.now()},
            )
            updated += 1
    logger.info(
        "Updated the condition of %d regions (%d failed)",
        updated,
        failed,
    )
    return updated, failed
