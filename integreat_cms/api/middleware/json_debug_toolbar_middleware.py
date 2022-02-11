"""
This module includes functions that extend the functionality of the Django Debug Toolbar to non HTML responses.
"""
import json
from django.http import HttpResponse


# pylint: disable=too-few-public-methods
class JsonDebugToolbarMiddleware:
    """
    The Django Debug Toolbar usually only works for views that return HTML.
    This middleware wraps any JSON response in HTML if the request
    has a 'debug' query parameter (e.g. http://localhost:8000/api/augsburg/de/pages?debug)
    """

    def __init__(self, get_response):
        """
        Initialize the middleware for the current view

        :param get_response: A callable to get the response for the current request
        :type get_response: ~collections.abc.Callable
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Call the middleware for the current request

        :param request: Django request
        :type request: ~django.http.HttpRequest

        :return: The modified response
        :rtype: ~django.http.HttpResponse
        """
        response = self.get_response(request)
        if "debug" in request.GET:
            if response["Content-Type"] == "application/json":
                content = json.dumps(
                    json.loads(response.content), sort_keys=True, indent=2
                )
                response = HttpResponse(
                    f"<!DOCTYPE html><html><body><pre>{content}</pre></body></html>"
                )

        return response
