from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.management.base import CommandError

from .log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class DebugCommand(LogCommand):
    """
    Base class for management commands which can only be executed in debug mode
    """

    def execute(self, *args: Any, **options: Any) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        if not settings.DEBUG:
            raise CommandError("This command can only be used in DEBUG mode.")
        super().execute(*args, **options)

    def handle(self, *args: Any, **options: Any) -> None:
        """
        The actual logic of the command. Subclasses must implement this method.
        """
        raise NotImplementedError(
            "subclasses of BaseCommand must provide a handle() method"
        )
