import threading
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

_request_local = threading.local()


def set_request(request: HttpRequest) -> None:
    """
    Set the current request in the thread-local storage.

    :param request: The current request object
    :return: None
    """
    _request_local.request = request


def get_request() -> HttpRequest | None:
    """
    Get the current request from the thread-local storage.

    :return: The current request object, or None if not set
    """
    return getattr(_request_local, "request", None)


class DebugRequestMiddleware:
    def __init__(self, get_response: Callable) -> None:
        """
        Initialize the middleware instance.

        :param get_response: The function to call to get the response
        :return: None
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Call the middleware for the given request.

        :param request: The current request object
        :return: The response object
        """
        set_request(request)
        return self.get_response(request)
