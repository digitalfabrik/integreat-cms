import logging
from datetime import datetime

from django.core.management.base import CommandError

from ....cms.models import Region
from ..log_command import LogCommand

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to reset DeepL budget
    """

    help = "Reset DeepL budget"

    def add_arguments(self, parser):
        """
        Define the arguments of this command

        :param parser: The argument parser
        :type parser: ~django.core.management.base.CommandParser
        """
        parser.add_argument(
            "--force",
            action="store_true",
            help="Whether the reset should be run despite it's not the 1st day of the month",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args, force, **options):
        """
        Try to run the command
        """

        current_day = datetime.now().day
        current_month = datetime.now().month - 1

        if current_day != 1 and not force:
            raise CommandError(
                "It is not the 1st day of the month. If you want to reset DeepL budget despite that, run the command with --force"
            )

        if not (regions := Region.objects.filter(deepl_renewal_month=current_month)):
            self.print_info(
                "✔ There is no region whose DeepL budget needs to be reset."
            )
        else:
            for region in regions:
                region.deepl_budget_used = 0
                region.deepl_midyear_start_month = None
                region.save()
            self.print_info("✔ DeepL budget has been reset.")
