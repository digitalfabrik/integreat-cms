import logging

from django.core.management.base import CommandError
from django.template.defaultfilters import filesizeformat

from ....cms.models import MediaFile
from ..log_command import LogCommand

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to find large media files
    """

    help = "Find large media files in the CMS"

    def add_arguments(self, parser):
        """
        Define the arguments of this command

        :param parser: The argument parser
        :type parser: ~django.core.management.base.CommandParser
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
    def handle(self, *args, limit, threshold, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param limit: Limit the result to this number
        :type limit: int

        :param threshold: Only show the files larger than this value
        :type threshold: float

        :param \**options: The supplied keyword options
        :type \**options: dict

        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        if threshold < 0:
            raise CommandError("The threshold cannot be negative.")
        if limit < 0:
            raise CommandError("The limit cannot be negative.")
        if limit > 100:
            raise CommandError("Please select a limit smaller than 100.")
        threshold_bytes = threshold * 1024 * 1024
        self.print_info(
            f"Searching the largest {limit} media with more than {threshold}MiB..."
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
                self.stdout.write(
                    f"{size:>{max_size_len}}: {self.cyan(name)} ({region})"
                )
        else:
            self.stdout.write("No files found with these filters.")
