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
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


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
            "--region-slug",
            help="The slug of the region to fetch page accesses from. Statistics need to be activated",
        )
        parser.add_argument("--sync")

    def handle(
        self,
        *args: Any,
        start_date: str,
        end_date: str,
        region_slug: str | None,
        sync: bool | None,
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
        except ValueError as e:
            raise CommandError("Wrong date format, please use YYYY-MM-DD") from e
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
        for region in regions:
            if sync:
                fetch_page_accesses(starting_date, ending_date, region)
            else:
                async_fetch_page_accesses.apply_async(
                    args=[starting_date, ending_date, region.id]
                )
