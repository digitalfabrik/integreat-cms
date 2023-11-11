from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils.termcolors import make_style


# pylint: disable=abstract-method
class LogCommand(BaseCommand):
    """
    Base class for management commands to improve the output
    """

    #: Make text bold
    bold = staticmethod(make_style(opts=("bold",)))
    #: Make text blue
    blue = staticmethod(make_style(fg="blue"))
    #: Make text cyan
    cyan = staticmethod(make_style(fg="cyan"))

    def print_info(self, message: str) -> None:
        """
        Print colored info message

        :param message: The message
        """
        self.stdout.write(self.bold(self.blue(message)))

    def print_success(self, message: str) -> None:
        """
        Print colored success message

        :param message: The message
        """
        self.stdout.write(self.style.SUCCESS(message))

    def print_error(self, message: str) -> None:
        """
        Print colored error message

        :param message: The message
        """
        self.stderr.write(self.style.ERROR(message))
