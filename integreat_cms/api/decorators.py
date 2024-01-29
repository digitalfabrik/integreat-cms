"""
This module includes functions that are used as decorators in the API endpoints.
"""

from __future__ import annotations

import json
import logging
import random
import re
import threading
from functools import wraps
from typing import TYPE_CHECKING
from urllib import error, parse, request

from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..cms.constants import feedback_ratings
from ..cms.models import Language, Region

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


def feedback_handler(func: Callable) -> Callable:
    """
    Decorator definition for feedback API functions and methods

    :param func: decorated function
    :return: The decorated feedback view function
    """

    @csrf_exempt
    @wraps(func)
    def handle_feedback(
        request: HttpRequest, region_slug: str, language_slug: str
    ) -> JsonResponse:
        """
        Parse feedback API request parameters

        :param request: Django request
        :param region_slug: slug of a region
        :param language_slug: slug of a language
        :return: The decorated feedback view function
        """
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request."}, status=405)
        try:
            region = Region.objects.get(slug=region_slug)
            language = Language.objects.get(slug=language_slug)
        except Region.DoesNotExist:
            return JsonResponse(
                {"error": f'No region found with slug "{region_slug}"'}, status=404
            )
        except Language.DoesNotExist:
            return JsonResponse(
                {"error": f'No language found with slug "{language_slug}"'}, status=404
            )
        data = (
            json.loads(request.body.decode())
            if request.content_type == "application/json"
            else request.POST.dict()
        )
        comment = data.pop("comment", "")
        rating = data.pop("rating", None)
        category = data.pop("category", None)

        if rating not in [None, "up", "down"]:
            return JsonResponse({"error": "Invalid rating."}, status=400)
        if not comment and not rating:
            return JsonResponse(
                {"error": "Either comment or rating is required."}, status=400
            )
        rating_normalized: bool | None = feedback_ratings.NOT_STATED
        if rating == "up":
            rating_normalized = feedback_ratings.POSITIVE
        elif rating == "down":
            rating_normalized = feedback_ratings.NEGATIVE
        is_technical = category == "Technisches Feedback"
        return func(data, region, language, comment, rating_normalized, is_technical)

    return handle_feedback


def json_response(function: Callable) -> Callable:
    """
    This decorator can be used to catch :class:`~django.http.Http404` exceptions and convert them to a :class:`~django.http.JsonResponse`.
    Without this decorator, the exceptions would be converted to :class:`~django.http.HttpResponse`.

    :param function: The view function which should always return JSON
    :return: The decorated function
    """

    @wraps(function)
    def wrap(
        request: dict[str, str] | HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect | JsonResponse:
        r"""
        The inner function for this decorator.
        It tries to execute the decorated view function and returns the unaltered result with the exception of a
        :class:`~django.http.Http404` error, which is converted into JSON format.

        :param request: Django request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied kwargs
        :return: The response of the given function or an 404 :class:`~django.http.JsonResponse`
        """
        try:
            return function(request, *args, **kwargs)
        except Http404 as e:
            return JsonResponse({"error": str(e) or "Not found."}, status=404)

    return wrap


def matomo_tracking(func: Callable) -> Callable:
    """
    This decorator is supposed to be applied to API content endpoints. It will track
    the request in Matomo. The request to the Matomo API is executed asynchronously in its
    own thread to not block the Integreat CMS API request.

    Only the URL and the User Agent will be sent to Matomo.

    :param func: decorated function
    :return: The decorated feedback view function
    """

    def matomo_request(host: str, data: dict) -> None:
        """
        Wrap HTTP request to Matomo in threaded function.

        :param host: Hostname + protocol of Matomo installation
        :param data: Data to send to Matomo API
        """
        data_str = parse.urlencode(data)
        url = f"{host}/matomo.php?{data_str}"
        req = request.Request(url)
        try:
            with request.urlopen(req):
                pass
        except error.HTTPError as e:
            logger.error(
                "Matomo Tracking API request to %r failed with: %s",
                # Mask auth token in log
                re.sub(r"&token_auth=[^&]+", "&token_auth=********", url),
                e,
            )

    @wraps(func)
    def wrap(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        r"""
        The inner function for this decorator.

        :param request: Django request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied kwargs
        :return: The response of the given function or an 404 :class:`~django.http.JsonResponse`
        """
        if (
            not settings.MATOMO_TRACKING
            or not request.region.matomo_id
            or not request.region.matomo_token
        ):
            return func(request, *args, **kwargs)
        data = {
            "idsite": request.region.matomo_id,
            "token_auth": request.region.matomo_token,
            "rec": 1,
            "url": request.build_absolute_uri(),
            "urlref": settings.BASE_URL,
            "ua": request.META.get("HTTP_USER_AGENT", "unknown user agent"),
            "cip": f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
        }

        t = threading.Thread(target=matomo_request, args=(settings.MATOMO_URL, data))
        t.daemon = True
        t.start()
        return func(request, *args, **kwargs)

    return wrap
