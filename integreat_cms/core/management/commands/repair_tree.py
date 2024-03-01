from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ....cms.utils.repair_tree import Printer, repair_tree
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to repair a broken Treebeard page tree
    """

    help = "Repair broken tree structure"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "--page_id",
            type=int,
            help="The ID of a page belonging to the broken tree (check all if omitted).",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Whether changes should be written to the database",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args: Any, page_id: int, commit: bool, **options: Any) -> None:
        """
        Try to run the command
        """
        printer = Printer(self.print_info, self.print_error, self.print_success)
        printer.bold = self.bold
        printer.write = self.stdout.write
        return repair_tree(page_id, commit, printer=printer)
