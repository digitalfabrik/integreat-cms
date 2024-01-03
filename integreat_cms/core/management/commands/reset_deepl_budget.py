from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from django.core.management.base import CommandError

from ....cms.models import Region
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to reset DeepL budget
    """

    help: str = "Reset DeepL budget"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "--force",
            action="store_true",
            help="Whether the reset should be run despite it's not the 1st day of the month",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args: Any, force: bool, **options: Any) -> None:
        """
        Try to run the command
        """
        self.set_logging_stream()

        now = datetime.now()
        current_day = now.day
        # month constants are zero-based
        current_month = now.month - 1
        current_month_name = now.strftime("%B")

        if current_day != 1:
            if force:
                logger.warning(
                    "Resetting DeepL budget although it is not the 1st day of the month (it's the %r)",
                    current_day,
                )
            else:
                raise CommandError(
                    "It is not the 1st day of the month. If you want to reset DeepL budget despite that, run the command with --force"
                )

        if not (regions := Region.objects.filter(deepl_renewal_month=current_month)):
            logger.info(
                "There is no region whose DeepL budget needs to be reset in %r.",
                current_month_name,
            )
        else:
            for region in regions:
                logger.info(
                    "Reset DeepL budget of %r (previously used: %r, previous midyear start month: %r).",
                    region,
                    region.deepl_budget_used,
                    region.deepl_midyear_start_month,
                )
                region.deepl_budget_used = 0
                region.deepl_midyear_start_month = None
                region.save()
            logger.success("✔ DeepL budget has been reset.")  # type: ignore[attr-defined]
