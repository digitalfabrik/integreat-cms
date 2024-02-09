"""
APIv3 endpoint for feedback bout single pages
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.http import Http404, JsonResponse

from ....cms.models import PageFeedback
from ...decorators import feedback_handler, json_response

if TYPE_CHECKING:
    from ....cms.models import Language, Region

logger = logging.getLogger(__name__)


@feedback_handler
@json_response
def page_feedback(
    data: dict[str, str],
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Decorate function for storing feedback about single page in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :return: decorated function that saves feedback in database
    """
    return page_feedback_internal(data, region, language, comment, rating, is_technical)


def page_feedback_internal(
    data: dict[str, str],
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Store feedback about single event in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :raises ~django.http.Http404: HTTP status 404 if no page with the given slug exists.

    :return: JSON object according to APIv3 single page feedback endpoint definition
    """
    page_translation_slug = data.get("slug")

    pages = region.pages.filter(
        translations__slug=data.get("slug"),
        translations__language=language,
    ).distinct()

    if len(pages) > 1:
        logger.error(
            "Page translation slug %r is not unique per region and language, found multiple: %r",
            page_translation_slug,
            pages,
        )
        return JsonResponse({"error": "Internal Server Error"}, status=500)
    if not pages:
        raise Http404("No matching page found for slug.")
    page = pages[0]
    page_translation = page.get_translation(language.slug)

    PageFeedback.objects.create(
        page_translation=page_translation,
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
