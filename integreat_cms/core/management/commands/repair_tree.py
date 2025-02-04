from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ....cms.utils.repair_tree import repair_tree
from ..log_command import LogCommand

if TYPE_CHECKING:
    from collections.abc import Iterable
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
            nargs="+",
            help="The ID(s) of one or more pages whose trees should be repaired (check all if omitted)",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Whether changes should be written to the database",
        )

    def handle(
        self, *args: Any, page_id: Iterable[int], commit: bool, **options: Any
    ) -> None:
        """
        Try to run the command
        """
        self.set_logging_stream()

        return repair_tree(page_id, commit, logging_name=logger.name)
