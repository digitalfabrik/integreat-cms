from django.conf import settings
from django.utils import timezone

# pylint: disable=too-few-public-methods
class TimezoneMiddleware:
    """
    Middleware class that sets the current time zone like specified in settings.py
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate(settings.CURRENT_TIME_ZONE)
        return self.get_response(request)
