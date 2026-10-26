"""
This module contains utilities to precompute the condition of regions

The metrics are calculated the same way as the columns of the region condition export, but
computing them runs heavy queries over all pages of a region. They are therefore computed once per
night and stored in :class:`~integreat_cms.cms.models.regions.region_condition.RegionCondition`.
The export and the region condition view are unchanged and still compute live.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from celery.exceptions import SoftTimeLimitExceeded
from django.db.models import F, Q
from django.test import override_settings
from django.utils import timezone

from ..constants import region_status
from ..models import Region, RegionCondition
from ..views.region_condition.region_condition_actions import RegionConditionResource

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


@contextmanager
def cacheops_disabled() -> Iterator[None]:
    """
    Disable the cacheops query cache for the duration of the block

    The metrics run large querysets over all pages of a region. Caching them is useless — every
    region is computed only once — and harmful: cacheops would store each of these results in
    Redis, several MB per key, which for all regions can exhaust the memory of Redis.

    ``override_settings`` sends ``setting_changed``, which cacheops listens to, so the override
    takes effect immediately. It is global to the process, which is safe in a prefork Celery worker
    or a management command but not in a threaded process. While it is active, cacheops does not
    invalidate on writes either, so only read inside this block.

    :return: A context in which queries bypass the cache
    """
    with override_settings(CACHEOPS_ENABLED=False):
        yield


def compute_region_condition(region: Region) -> dict[str, int]:
    """
    Compute the condition metrics of a region

    The computation reuses the ``dehydrate_*`` methods of the region condition export, so both
    calculate their numbers the same way.

    :param region: The region whose condition should be computed
    :return: The metrics of the region, keyed like the fields of the region condition model
    """
    with cacheops_disabled():
        return {
            metric: getattr(RegionConditionResource, f"dehydrate_{metric}")(region)
            for metric in RegionCondition.METRICS
        }


def update_region_conditions() -> tuple[int, list[str]]:
    """
    Compute and store the condition of all active and hidden regions

    A failure in one region is logged and does not stop the others, so a single broken region
    cannot leave all other regions with stale numbers. The regions with the oldest values are
    computed first, so a run that is cut short by the time limit does not always miss the same
    regions. Stored values of regions which are no longer active or hidden are removed, so the API
    does not keep serving them.

    :raises ~celery.exceptions.SoftTimeLimitExceeded: When the Celery task runs out of time
    :return: The number of updated regions and the slugs of the failed regions
    """
    regions = Region.objects.filter(
        Q(status=region_status.ACTIVE) | Q(status=region_status.HIDDEN),
    ).order_by(F("condition__computed_at").asc(nulls_first=True), "slug")
    RegionCondition.objects.exclude(region__in=regions).delete()

    updated = 0
    failed: list[str] = []
    remaining = list(regions)
    for region in list(remaining):
        try:
            metrics = compute_region_condition(region)
            # Written outside of the cacheops block, so the cached API read is invalidated
            RegionCondition.objects.update_or_create(
                region=region,
                defaults={**metrics, "computed_at": timezone.now()},
            )
        except SoftTimeLimitExceeded:
            logger.exception(
                "Ran out of time, the condition of these regions was not updated: %s",
                ", ".join(r.slug for r in remaining),
            )
            raise
        except Exception:
            logger.exception("Could not compute the condition of %r", region)
            failed.append(region.slug)
        else:
            updated += 1
        remaining.remove(region)
    logger.info(
        "Updated the condition of %d regions (%d failed)",
        updated,
        len(failed),
    )
    return updated, failed
