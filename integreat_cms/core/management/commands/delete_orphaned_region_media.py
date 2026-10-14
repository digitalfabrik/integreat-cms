from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings

from ....cms.models import Region
from ....cms.utils.media_utils import delete_region_media_directory
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to delete media directories of regions which do not exist anymore
    """

    help = "Delete media directories of regions which do not exist anymore"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only list the orphaned media directories without deleting them",
        )

    def handle(self, *args: Any, dry_run: bool, **options: Any) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param dry_run: Whether the directories should only be listed
        :param \**options: The supplied keyword options
        """
        self.set_logging_stream()
        regions_directory = Path(settings.MEDIA_ROOT) / "regions"
        if not regions_directory.is_dir():
            logger.info("No region media directory found at %s.", regions_directory)
            return
        region_ids = set(Region.objects.values_list("id", flat=True))
        orphaned_region_ids = []
        for directory in sorted(regions_directory.iterdir()):
            if not directory.is_dir():
                continue
            # Only accept canonical region ids, so the directory path can be rebuilt from the id
            if not re.fullmatch(r"[1-9][0-9]*", directory.name):
                logger.warning("Skipping unexpected directory %s", directory)
                continue
            if int(directory.name) not in region_ids:
                orphaned_region_ids.append(int(directory.name))
        if not orphaned_region_ids:
            logger.info("No orphaned region media directories found.")
            return
        for region_id in orphaned_region_ids:
            directory = regions_directory / str(region_id)
            if dry_run:
                logger.info("Found orphaned media directory %s", directory)
            elif delete_region_media_directory(region_id):
                logger.info("Deleted orphaned media directory %s", directory)
            else:
                logger.error("Could not delete orphaned media directory %s", directory)
