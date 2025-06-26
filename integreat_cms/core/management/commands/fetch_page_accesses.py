from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from django.core.management.base import CommandError

from integreat_cms.cms.constants.region_status import ACTIVE
from integreat_cms.cms.views.statistics.statistics_actions import (
    async_fetch_page_accesses,
    fetch_page_accesses,
)

from ....cms.models import Region
from ..log_command import LogCommand

if TYPE_CHECKING:
    from datetime import date
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


def start_fetch_page_accesses(
    start_date: date,
    end_date: date,
    period: str,
    regions: list[Region],
    synchronous: bool | None,
) -> None:
    """
    Load page accesses from Matomo and save them to page accesses model

    :param start_date: Earliest date
    :param end_date: Latest date
    :param period: The period (one of :attr:`~integreat_cms.cms.constants.matomo_periods.CHOICES`)
    :param regions: The regions for which we want our page based accesses
    """
    if not synchronous:
        for region in regions:
            async_fetch_page_accesses.apply_async(
                args=[start_date, end_date, period, region.id]
            )
    if synchronous:
        for region in regions:
            fetch_page_accesses(
                start_date=start_date, end_date=end_date, period=period, region=region
            )


class Command(LogCommand):
    """
    Management command to fetch page accesses from matomo
    """

    help: str = (
        "Fetches page accesses from Matomo and store them in them in the database"
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument("--start-date", required=True, help="Earliest date")
        parser.add_argument("--end-date", required=True, help="Latest date")
        parser.add_argument(
            "--period", required=True, help="Period. Needs to be day, week or month"
        )
        parser.add_argument(
            "--region-slug",
            help="The slug of the region to fetch page accesses from. Statistics need to be activatet",
        )
        parser.add_argument(
            "--synchronous",
            type=bool,
            help="Whether page accesses should be fetched asynchronous, defaults to True",
        )

    def handle(
        self,
        *args: Any,
        start_date: str,
        end_date: str,
        period: str,
        region_slug: str | None,
        synchronous: bool | None,
        **options: Any,
    ) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param start_date: The earliest date
        :param end_date: The latest date
        :param period: The period (one of :attr:`~integreat_cms.cms.constants.matomo_periods.CHOICES`)
        :param region_slug: The slug of the given region
        :param \**options: The supplied keyword options
        """
        self.set_logging_stream()
        regions = []
        try:
            starting_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            ending_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            if region_slug is not None:
                try:
                    regions.append(Region.objects.get(slug=region_slug))
                except Region.DoesNotExist as e:
                    raise CommandError(
                        f'Region with slug "{region_slug}" does not exist.',
                    ) from e
                if not regions[0].statistics_enabled:
                    logger.error("Statistics are not enabled for this region.")
                    raise CommandError(f"Statistics are disabled in {regions[0].slug}.")
            else:
                regions = list(
                    Region.objects.filter(statistics_enabled=True, status=ACTIVE)
                )
            start_fetch_page_accesses(
                start_date=starting_date,
                end_date=ending_date,
                period=period,
                regions=regions,
                synchronous=synchronous,
            )
        except ValueError as e:
            raise CommandError("Wrong date format, please use YYYY-MM-DD") from e
