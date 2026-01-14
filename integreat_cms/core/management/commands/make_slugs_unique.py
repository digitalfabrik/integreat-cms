import logging
from typing import Any

from django.core.management.base import CommandError, CommandParser

from integreat_cms.cms.utils.slug_utils import (
    ALLOWED_OBJECTS,
    DEFAULT_OBJECTS,
    make_all_slugs_unique,
)
from integreat_cms.core.management.log_command import LogCommand

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to generate unique slugs for all translation objects
    """

    help = "Generates unique slugs for all translation objects"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "--objects",
            nargs="+",
            default=DEFAULT_OBJECTS,
            help="The objects for which the translations slug should be updated ",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do a dry-run, without commiting to the database",
        )

    def handle(
        self,
        **options: Any,
    ) -> None:
        objects = tuple(options["objects"])
        dry_run = options["dry_run"]

        invalid = [obj for obj in objects if obj not in ALLOWED_OBJECTS]
        if invalid:
            raise CommandError(
                f"Invalid models for make_slugs_unique command: {', '.join(sorted(invalid))}"
            )
        make_all_slugs_unique.delay(objects, dry_run)

        logger.info("Queued task make_all_slugs_unique")
