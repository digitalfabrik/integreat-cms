from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.base import CommandError

from ....cms.utils.region_condition_utils import update_region_conditions
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any


class Command(LogCommand):
    """
    Management command to precompute the condition of all active and hidden regions
    """

    help = "Compute and store the condition metrics of all active and hidden regions"

    def handle(self, *args: Any, **options: Any) -> None:
        r"""
        Compute and store the condition of all active and hidden regions

        :param \*args: The supplied arguments
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the condition of a region could
                                                           not be computed
        """
        self.set_logging_stream()
        _updated, failed = update_region_conditions()
        if failed:
            raise CommandError(
                f"The condition of {len(failed)} region(s) could not be computed: "
                f"{', '.join(failed)}",
            )
