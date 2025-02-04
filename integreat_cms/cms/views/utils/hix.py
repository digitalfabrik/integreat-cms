"""
This file contains functionality to communicate with the Textlab api to get the hix-value
for a given text.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import TYPE_CHECKING
from urllib.error import URLError

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from lxml.etree import LxmlError
from lxml.html import fromstring, tostring

from integreat_cms.cms.models.pages.page_translation import PageTranslation
from integreat_cms.cms.utils.round_hix_score import round_hix_score

from ....api.decorators import json_response
from ....textlab_api.textlab_api_client import TextlabClient, TextlabResult

if TYPE_CHECKING:
    from typing import Any, Final

    from django.db.models.query import QuerySet
    from django.http import HttpRequest

    from integreat_cms.cms.models.regions.region import Region

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH: Final[int] = 100_000


class CacheMeIfYouCan(Exception):
    """
    Helper exception used for stopping @lru_cache from caching
    """


@lru_cache(maxsize=512)
def lookup_hix_score_helper(text: str) -> TextlabResult:
    """
    This function returns the hix score for the given text.
    It either performs an api request or returns the value from cache,
    unless it is None, in which case an exception is raised to prevent
    caching.

    :param text: The text to calculate the hix score for
    :return: The score for the given text
    """
    try:
        html = fromstring(text)

        # remove divs which the authors have no control over (e.g. contact cards)
        for div in html.xpath('//div[@contenteditable="false"]'):
            div.getparent().remove(div)

        text_content = html.text_content()
        if not text_content.strip():
            return {
                "score": None,
                "feedback": [],
            }

        text = tostring(html, encoding="unicode")
    except LxmlError:
        pass

    # Replace all line breaks with <br> because Textlab API returns different HIX value depending on the line break character
    normalized_text = "<br>".join(text.splitlines())

    try:
        return TextlabClient(
            settings.TEXTLAB_API_USERNAME,
            settings.TEXTLAB_API_KEY,
        ).benchmark(normalized_text)
    except (URLError, OSError) as e:
        logger.warning("HIX benchmark API call failed: %r", e)
        raise CacheMeIfYouCan from e


def lookup_hix_score(text: str) -> TextlabResult | None:
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
def get_hix_score(
    request: HttpRequest,
    **kwargs: Any,
) -> JsonResponse:
    """
    Calculates the hix score for the param 'text' in the request body and returns it.

    :param request: The request
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

    if response := lookup_hix_score(text):
        return JsonResponse(
            {
                "score": round_hix_score(response.get("score")),
                "feedback": response.get("feedback"),
            },
        )

    return JsonResponse({"error": "Could not retrieve hix score"})


def get_translations_relevant_to_hix(region: Region) -> QuerySet:
    """
    Get page translations for a region sorted by hix score.

    :param region: The region for which to get all of the translations
    """
    if not settings.TEXTLAB_API_ENABLED or not region.hix_enabled:
        return PageTranslation.objects.none()

    return PageTranslation.objects.filter(
        id__in=(
            PageTranslation.objects.filter(
                language__slug__in=settings.TEXTLAB_API_LANGUAGES,
                page__in=region.get_pages().filter(hix_ignore=False),
            ).distinct("page_id", "language_id")
        ),
    ).order_by("hix_score")


HIX_ROUNDING_PRECISION = 0.01
ACTUAL_RAW_HIX_SCORE_THRESHOLD = (
    settings.HIX_REQUIRED_FOR_MT - HIX_ROUNDING_PRECISION / 2
)


def get_translation_under_hix_threshold(
    region: Region,
) -> QuerySet:
    """
    Filter page translations which are under the hix threshold

    :param region: The region for which to get all of the translations
    """
    return get_translations_relevant_to_hix(
        region=region,
    ).filter(hix_score__lt=ACTUAL_RAW_HIX_SCORE_THRESHOLD)


def get_translation_over_hix_threshold(
    region: Region,
) -> QuerySet:
    """
    Filter page translations which are over the hix threshold

    :param region: The region for which to get all of the translations
    """
    return get_translations_relevant_to_hix(region=region).filter(
        hix_score__gte=ACTUAL_RAW_HIX_SCORE_THRESHOLD,
    )
