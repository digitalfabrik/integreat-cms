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
from django.db import connection, InterfaceError, OperationalError
from django.db.models import F, Max
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

    The metrics run large querysets over all pages of a region. Caching them would store several
    MB per region in Redis, which can exhaust its memory. The override is global to the process
    and also disables the invalidation on writes, so only read inside this block.

    :return: A context in which queries bypass the cache
    """
    try:
        with override_settings(CACHEOPS_ENABLED=False):
            yield
    finally:
        # Otherwise an interrupted restore would keep cacheops disabled for the worker process
        cacheops.conf.settings.__dict__.pop("CACHEOPS_ENABLED", None)


def compute_region_condition(region: Region) -> dict[str, int]:
    """
    Compute the condition metrics of a region with the ``dehydrate_*`` methods of the export

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

    A failure in one region is logged and does not stop the others. Regions without stored values
    and then those with the oldest values are computed first, so a run that is cut short does not
    always miss the same regions. Every successful computation adds a row, so the history is kept.

    :param time_budget: The number of seconds after which no further region is started
    :raises ~django.db.Error: When the database connection is lost
    :raises ~celery.exceptions.SoftTimeLimitExceeded: When Celery's time limit is hit anyway
    :return: The outcome of the run
    """
    deadline = time.monotonic() + time_budget if time_budget is not None else None
    regions = (
        Region.objects.filter(status__in=COMPUTED_STATUSES)
        .annotate(last_computed_at=Max("conditions__computed_at"))
        .order_by(F("last_computed_at").asc(nulls_first=True), "slug")
    )

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
                # The region might have been archived during the computation
                if Region.objects.filter(
                    pk=region.pk,
                    status__in=COMPUTED_STATUSES,
                ).exists():
                    # Outside of cacheops_disabled(), so the cached read of the API is invalidated
                    RegionCondition.objects.create(
                        region=region,
                        computed_at=timezone.now(),
                        **metrics,
                    )
                    result.updated += 1
            except (SoftTimeLimitExceeded, InterfaceError):
                raise
            except Exception as error:
                # Timeouts, deadlocks etc. only concern this region, a lost connection all of them
                if isinstance(error, OperationalError) and not connection.is_usable():
                    raise
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
