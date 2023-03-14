import logging

from django.conf import settings
from django.core.management.base import CommandError

from .log_command import LogCommand

logger = logging.getLogger(__name__)


# pylint: disable=abstract-method
class DebugCommand(LogCommand):
    """
    Base class for management commands which can only be executed in debug mode
    """

    def execute(self, *args, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**options: The supplied keyword options
        :type \**options: dict

        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        if not settings.DEBUG:
            raise CommandError("This command can only be used in DEBUG mode.")
        super().execute(*args, **options)
