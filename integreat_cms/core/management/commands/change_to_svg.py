import csv
import select
import sys
from typing import Any

from django.core.management.base import CommandParser

from integreat_cms.cms.models.media.media_file import MediaFile

from ..log_command import LogCommand


class Command(LogCommand):
    """
    Management command to change references from .png or .jpeg to .svg
    """

    help = "Change the reference from .png icons to .svg icons, if they share the same name"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "path",
            nargs="?",
            default=None,
            help="The path to the csv file we want to import from",
        )

    def should_stdin_be_used(self, options: dict) -> bool:
        return (
            sys.platform != "win32"
            and not sys.stdin.isatty()
            and select.select([sys.stdin], [], [], 0)[0]
            and not options["path"]
        )

    def handle(self, *args: Any, **options: Any) -> None:
        with (
            open(options["path"], newline="")
            if not self.should_stdin_be_used(options)
            else sys.stdin as csvfile
        ):
            reader = csv.reader(csvfile, delimiter=",", quotechar="|")
            next(reader, None)
            for row in reader:
                old_path = (
                    row[0]
                    .removeprefix("https://")
                    .removeprefix("admin.integreat-app.de/media/")
                    .removeprefix("cms.integreat-app.de/media/")
                )
                new_path = (
                    row[1]
                    .removeprefix("https://")
                    .removeprefix("admin.integreat-app.de/media/")
                    .removeprefix("cms.integreat-app.de/media/")
                )
                try:
                    old_media_file = MediaFile.objects.get(file=old_path)
                    new_media_file = MediaFile.objects.get(file=new_path)
                    print(old_media_file, new_media_file)
                except MediaFile.DoesNotExist:
                    print(
                        f"Either old or new path not valid. Old path was {old_path} and new path was {old_path}"
                    )

        # change reference from .png or .jpeg to .svg (if existant)
        """pages = Page.objects.filter(explicitly_archived=False).exclude(icon=None)
        for page in pages:
            print(page.icon)"""
