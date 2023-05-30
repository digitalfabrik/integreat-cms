"""
This file contains functionality to communicate with the Textlab api to get the hix-value
for a given text.
"""

import json
import logging
from functools import lru_cache
from urllib.error import URLError

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from lxml.etree import LxmlError
from lxml.html import fromstring, tostring

from ....api.decorators import json_response
from ....textlab_api.textlab_api_client import TextlabClient

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 100_000


@lru_cache(maxsize=512)
def lookup_hix_score(text):
    """
    This function returns the hix score for the given text.
    It either performs an api request or returns the value from cache.

    :param text: The text to calculate the hix score for
    :type text: str

    :return: The score for the given text
    :rtype: float
    """
    try:
        return TextlabClient(
            settings.TEXTLAB_API_USERNAME, settings.TEXTLAB_API_KEY
        ).benchmark(text)
    except (URLError, OSError) as e:
        logger.warning("HIX benchmark API call failed: %r", e)
        return None


@require_POST
@json_response
# pylint: disable=unused-argument
def get_hix_score(request, region_slug):
    """
    Calculates the hix score for the param 'text' in the request body and returns it.

    :param request: The request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: A json response, of {"score": value} in case of success
    :rtype: ~django.http.JsonResponse
    """
    # Don't pass texts larger than 100kb to the api in order to avoid being vulnerable to dos attacks
    if len(request.body) > MAX_TEXT_LENGTH:
        return JsonResponse({"error": "Request too large"})

    body = json.loads(request.body.decode("utf-8"))
    text = body["text"]

    if not isinstance(text, str) or not text.strip():
        logger.warning("Received invalid text: %r", text)
        return JsonResponse({"error": f"Invalid text: '{text}'"})

    # Normalize text to get same HIX result as with form submission
    text = text.replace("\n", "\r\n")
    try:
        text = tostring(fromstring(text)).decode("utf-8")
    except LxmlError:
        pass

    if score := lookup_hix_score(text):
        return JsonResponse({"score": score})
    return JsonResponse({"error": "Could not retrieve hix score"})
