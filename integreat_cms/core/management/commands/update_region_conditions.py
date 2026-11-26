from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.base import CommandError

from ....cms.utils.region_condition_utils import update_region_conditions
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser


class Command(LogCommand):
    """
    Management command to precompute the condition of all active and hidden regions
    """

    help = "Compute and store the condition metrics of all active and hidden regions"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "--time-budget",
            type=float,
            default=None,
            help="Do not start further regions after this many seconds",
        )

    def handle(self, *args: Any, time_budget: float | None, **options: Any) -> None:
        r"""
        Compute and store the condition of all active and hidden regions

        :param \*args: The supplied arguments
        :param time_budget: The number of seconds after which no further region is started
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the condition of a region could
                                                           not be computed or was not reached
        """
        self.set_logging_stream()
        result = update_region_conditions(time_budget=time_budget)
        problems = []
        if result.failed:
            problems.append(
                f"could not be computed for {', '.join(result.failed)}",
            )
        if result.not_reached:
            problems.append(
                f"was not reached in time for {', '.join(result.not_reached)}",
            )
        if problems:
            raise CommandError(
                f"The region condition {'; '.join(problems)} (see the log file for details).",
            )
