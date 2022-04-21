from django.conf import settings
from django.utils import timezone


# pylint: disable=too-few-public-methods
class TimezoneMiddleware:
    """
    Middleware class that sets the current time zone like specified in settings.py
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

        :return: The response after the local timezone has been activated
        :rtype: ~django.http.HttpResponse
        """
        if request.region:
            timezone.activate(request.region.timezone)
        else:
            timezone.activate(settings.CURRENT_TIME_ZONE)
        return self.get_response(request)
