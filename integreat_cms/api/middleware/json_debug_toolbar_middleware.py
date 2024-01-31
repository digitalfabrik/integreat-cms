"""
This module includes functions that extend the functionality of the Django Debug Toolbar to non HTML responses.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from django.http import HttpResponse

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from asgiref.sync import AsyncToSync
    from django.http import HttpRequest


# pylint: disable=too-few-public-methods
class JsonDebugToolbarMiddleware:
    """
    The Django Debug Toolbar usually only works for views that return HTML.
    This middleware wraps any JSON response in HTML if the request
    has a 'debug' query parameter (e.g. http://localhost:8000/api/v3/augsburg/de/pages?debug)
    """

    def __init__(self, get_response: Callable | AsyncToSync) -> None:
        """
        Initialize the middleware for the current view

        :param get_response: A callable to get the response for the current request
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> Any:
        """
        Call the middleware for the current request

        :param request: Django request
        :return: The modified response
        """
        response = self.get_response(request)
        if "debug" in request.GET and response["Content-Type"] == "application/json":
            content = json.dumps(json.loads(response.content), sort_keys=True, indent=2)
            response = HttpResponse(
                f"<!DOCTYPE html><html><body><pre>{content}</pre></body></html>"
            )

        return response
