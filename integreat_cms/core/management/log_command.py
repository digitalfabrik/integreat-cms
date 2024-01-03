from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand

if TYPE_CHECKING:
    from typing import Any


logger = logging.getLogger("integreat_cms.core.management.commands")


class LogCommand(BaseCommand):
    """
    Base class for management commands to set the stream handler of the logger to the command's stdout wrapper
    """

    def handle(self, *args: Any, **options: Any) -> None:
        """
        The actual logic of the command. Subclasses must implement this method.
        """
        raise NotImplementedError(
            "subclasses of BaseCommand must provide a handle() method"
        )

    def set_logging_stream(self) -> None:
        """
        Set the output stream to the command's stdout/stderr wrapper.
        Has to be called as part of the command's handle() function.
        """
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                if handler.get_name() == "management-command-stdout":
                    handler.setStream(self.stdout)
                elif handler.get_name() == "management-command-stderr":
                    handler.setStream(self.stderr)
