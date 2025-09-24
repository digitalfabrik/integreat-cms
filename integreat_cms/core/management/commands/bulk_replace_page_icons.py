import csv
import logging
import select
import sys
from typing import Any

from django.core.management.base import CommandParser

from integreat_cms.cms.models.media.media_file import MediaFile
from integreat_cms.cms.models.pages.page import Page

from ..log_command import LogCommand

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to change references of media files from a source path to a target path.
    This command reads a CSV file and then changes the reference from the first and second column (source region and path)
    to the one of the third and fourth column (target region and path).
    """

    help = "Replace references of media files from source paths with target paths based on a CSV file."

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "csv",
            nargs="?",
            default=None,
            help="The path to the csv file we want to read the replacements from",
        )

    def should_stdin_be_used(self, options: dict) -> bool:
        return bool(
            sys.platform != "win32"
            and not sys.stdin.isatty()
            and select.select([sys.stdin], [], [], 0)[0]
            and not options["csv"]
        )

    def handle(self, *args: Any, **options: Any) -> None:
        successful = 0
        failed = 0

        with (
            open(options["csv"], newline="")
            if not self.should_stdin_be_used(options)
            else sys.stdin as csvfile
        ):
            reader = csv.reader(csvfile, delimiter=",", quotechar="|")
            next(reader, None)

            for row in reader:
                path = {
                    "old": (
                        row[0]
                        .removeprefix("https://")
                        .removeprefix("admin.integreat-app.de/media/")
                        .removeprefix("cms.integreat-app.de/media/")
                    ),
                    "new": (
                        row[1]
                        .removeprefix("https://")
                        .removeprefix("admin.integreat-app.de/media/")
                        .removeprefix("cms.integreat-app.de/media/")
                    ),
                }
                file = {"old": None, "new": None}

                for which, p in path.items():
                    try:
                        file[which] = MediaFile.objects.get(
                            file=p,
                        )
                    except MediaFile.DoesNotExist:
                        logger.info(
                            "%r path is not valid. Old path was %r and new path was %r",
                            which,
                            path["old"],
                            path["new"],
                        )

                if file["old"] and file["new"]:
                    pages = Page.objects.filter(
                        explicitly_archived=False, icon=file["old"]
                    )
                    for page in pages:
                        logger.info("page %r found", page)
                        page.icon = file["new"]
                        page.save()

                    successful += 1
                else:
                    failed += 1

        logger.info("DONE  Replaced %r files (%r failed)", successful, failed)
