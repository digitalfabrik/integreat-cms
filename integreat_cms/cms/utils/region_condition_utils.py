"""
This module contains utilities to precompute the condition of regions

The metrics are calculated the same way as the columns of the region condition export, but
computing them runs heavy queries over all pages of a region. They are therefore computed once per
night and stored in :class:`~integreat_cms.cms.models.regions.region_condition.RegionCondition`.
The export and the region condition view are unchanged and still compute live.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import cacheops.conf
from celery.exceptions import SoftTimeLimitExceeded
from django.db import InterfaceError, OperationalError
from django.db.models import F
from django.test import override_settings
from django.utils import timezone

from ..constants import region_status
from ..models import Region, RegionCondition
from ..views.region_condition.region_condition_actions import RegionConditionResource

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)

#: The statuses of the regions whose condition is computed and served
COMPUTED_STATUSES = [region_status.ACTIVE, region_status.HIDDEN]


@dataclass
class UpdateResult:
    """
    The outcome of a run of :func:`update_region_conditions`
    """

    #: The number of regions whose condition was stored
    updated: int = 0
    #: The slugs of the regions whose computation failed
    failed: list[str] = field(default_factory=list)
    #: The slugs of the regions which were not reached before the time budget ran out
    not_reached: list[str] = field(default_factory=list)


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
    try:
        with override_settings(CACHEOPS_ENABLED=False):
            yield
    finally:
        # cacheops memoizes the setting and only forgets it on ``setting_changed``. If an
        # asynchronous exception (e.g. Celery's soft time limit) interrupted the restore before
        # that signal, cacheops would stay disabled — and stop invalidating — for the rest of
        # the worker process.
        cacheops.conf.settings.__dict__.pop("CACHEOPS_ENABLED", None)


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


def update_region_conditions(time_budget: float | None = None) -> UpdateResult:
    """
    Compute and store the condition of all active and hidden regions

    A failure in one region is logged and does not stop the others, so a single broken region
    cannot leave all other regions with stale numbers. Regions without stored values and then
    those with the oldest values are computed first, so a run that is cut short does not always
    miss the same regions. Stored values of regions which are no longer active or hidden are
    removed, so the API does not keep serving them.

    :param time_budget: The number of seconds after which no further region is started. Checking
                        this between regions keeps a run from being interrupted in the middle of
                        a computation by Celery's time limit, which is only a last resort.
    :raises ~django.db.Error: When the database connection fails, which is not a problem of a single
                              region and would otherwise fail every remaining one
    :raises ~celery.exceptions.SoftTimeLimitExceeded: When Celery's time limit is hit anyway
    :return: The outcome of the run
    """
    deadline = time.monotonic() + time_budget if time_budget is not None else None
    regions = Region.objects.filter(status__in=COMPUTED_STATUSES).order_by(
        F("condition__computed_at").asc(nulls_first=True),
        "slug",
    )
    RegionCondition.objects.exclude(region__status__in=COMPUTED_STATUSES).delete()

    result = UpdateResult()
    remaining = list(regions)
    try:
        while remaining:
            if deadline is not None and time.monotonic() > deadline:
                result.not_reached = [region.slug for region in remaining]
                break
            region = remaining[0]
            try:
                metrics = compute_region_condition(region)
                # Only store if the region was not archived or deleted during the run
                if Region.objects.filter(
                    pk=region.pk,
                    status__in=COMPUTED_STATUSES,
                ).exists():
                    # Written outside of cacheops_disabled(): with CACHEOPS_ENABLED=False
                    # cacheops skips invalidation, and the cached read of the API would serve
                    # the old values for up to an hour
                    RegionCondition.objects.update_or_create(
                        region=region,
                        defaults={**metrics, "computed_at": timezone.now()},
                    )
                    result.updated += 1
            except (SoftTimeLimitExceeded, InterfaceError, OperationalError):
                raise
            except Exception:
                logger.exception("Could not compute the condition of %r", region)
                result.failed.append(region.slug)
            remaining.pop(0)
    except (SoftTimeLimitExceeded, InterfaceError, OperationalError):
        result.not_reached = [region.slug for region in remaining]
        logger.exception(
            "Aborted the update of the region conditions; not updated: %s; failed before: %s",
            ", ".join(result.not_reached),
            ", ".join(result.failed) or "none",
        )
        raise

    if result.not_reached:
        logger.error(
            "Ran out of time, the condition of these regions was not updated: %s",
            ", ".join(result.not_reached),
        )
    logger.info(
        "Updated the condition of %d regions (%d failed, %d not reached)",
        result.updated,
        len(result.failed),
        len(result.not_reached),
    )
    return result
