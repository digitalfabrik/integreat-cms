"""
This file contains functionality to communicate with the Textlab api to get the hix-value
for a given text.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import TYPE_CHECKING
from urllib.error import HTTPError

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ....api.decorators import json_response
from ....textlab_api.textlab_api_client import TextlabClient

if TYPE_CHECKING:
    from typing import Final

    from django.http import HttpRequest

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH: Final[int] = 100_000


class CacheMeIfYouCan(Exception):
    """
    Helper exception used for stopping @lru_cache from caching
    """


def log_hix_error_message(error: OSError) -> None:
    """
    Logging of error details returned by the TextLab API
    """
    error_message = f"HIX benchmark API call failed: '{error}'"

    if isinstance(error, HTTPError):
        error_response = error.fp.read().decode("utf-8")
        try:
            data = json.loads(error_response)
            if "message" in data:
                error_message = error_message + " - " + data["message"]
        except ValueError:
            pass

    logger.warning(error_message)


@lru_cache(maxsize=512)
def lookup_hix_score_helper(text: str) -> float | None:
    """
    This function returns the hix score for the given text.
    It either performs an api request or returns the value from cache,
    unless it is None, in which case an exception is raised to prevent
    caching.

    :param text: The text to calculate the hix score for
    :return: The score for the given text
    """
    # Replace all line breaks with <br> because Textlab API returns different HIX value depending on the line break character
    normalized_text = "<br>".join(text.splitlines())

    try:
        return TextlabClient(
            settings.TEXTLAB_API_USERNAME, settings.TEXTLAB_API_KEY
        ).benchmark(normalized_text)
    except OSError as e:
        log_hix_error_message(e)
        raise CacheMeIfYouCan from e


def lookup_hix_score(text: str) -> float | None:
    """
    This function returns the hix score for the given text.
    It either performs an api request or returns the value from cache.

    :param text: The text to calculate the hix score for
    :return: The score for the given text
    """
    try:
        return lookup_hix_score_helper(text)
    except CacheMeIfYouCan:
        return None


@require_POST
@json_response
# pylint: disable=unused-argument
def get_hix_score(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Calculates the hix score for the param 'text' in the request body and returns it.

    :param request: The request
    :param region_slug: The slug of the current region
    :return: A json response, of {"score": value} in case of success
    """
    # Don't pass texts larger than 100kb to the api in order to avoid being vulnerable to dos attacks
    if len(request.body) > MAX_TEXT_LENGTH:
        return JsonResponse({"error": "Request too large"})

    body = json.loads(request.body.decode("utf-8"))
    text = body["text"]

    if not isinstance(text, str) or not text.strip():
        logger.warning("Received invalid text: %r", text)
        return JsonResponse({"error": f"Invalid text: '{text}'"})

    if score := lookup_hix_score(text):
        return JsonResponse({"score": score})
    return JsonResponse({"error": "Could not retrieve hix score"})
