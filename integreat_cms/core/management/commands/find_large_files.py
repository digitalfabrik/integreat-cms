from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.management.base import CommandError
from django.template.defaultfilters import filesizeformat

from ....cms.models import MediaFile
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to find large media files
    """

    help = "Find large media files in the CMS"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Only show the largest n files (max 100, defaults to 10)",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=3,
            help="Only show files larger than this threshold (in MiB, defaults to 3.0)",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args: Any, limit: int, threshold: int, **options: Any) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param limit: Limit the result to this number
        :param threshold: Only show the files larger than this value
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        self.set_logging_stream()
        if threshold < 0:
            raise CommandError("The threshold cannot be negative.")
        if limit < 0:
            raise CommandError("The limit cannot be negative.")
        if limit > 100:
            raise CommandError("Please select a limit smaller than 100.")
        threshold_bytes = threshold * 1024 * 1024
        logger.info(
            "Searching the largest %s media with more than %sMiB...", limit, threshold
        )
        if queryset := MediaFile.objects.filter(file_size__gt=threshold_bytes).order_by(
            "-file_size"
        )[:limit]:
            file_info = [
                (filesizeformat(file.file_size), file.name, file.region or "global")
                for file in queryset
            ]
            # Get the max len to enable right-aligned padding
            max_size_len = max(len(size) for size, _, _ in file_info)
            for size, name, region in file_info:
                logger.info(f"%{max_size_len}s: %s (%r)", size, name, region)
        else:
            logger.info("No files found with these filters.")
