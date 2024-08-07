from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.http import HttpRequest

from django.conf import settings
from django.utils import timezone


# pylint: disable=too-few-public-methods
class TimezoneMiddleware:
    """
    Middleware class that sets the current time zone like specified in settings.py
    """

    def __init__(self, get_response: Callable) -> None:
        """
        Initialize the middleware for the current view

        :param get_response: A callable to get the response for the current request
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> Any:
        """
        Call the middleware for the current request

        :param request: Django request
        :return: The response after the local timezone has been activated
        """
        if request.region:
            timezone.activate(request.region.timezone)
        else:
            timezone.activate(settings.CURRENT_TIME_ZONE)
        return self.get_response(request)
