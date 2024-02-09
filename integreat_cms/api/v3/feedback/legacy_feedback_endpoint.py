"""
APIv3 legacy feedback endpoint for pages, events and imprint
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.http import JsonResponse

if TYPE_CHECKING:
    from ....cms.models import Language, Region

from ...decorators import feedback_handler, json_response
from .event_feedback import event_feedback_internal
from .imprint_page_feedback import imprint_page_feedback_internal
from .page_feedback import page_feedback_internal


@feedback_handler
@json_response
def legacy_feedback_endpoint(
    data: dict[str, str],
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Decorate function for storing feedback about single page, imprint or event in database. This
    is a legacy endpoint for compatibility.

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :return: decorated function that saves feedback in database
    """
    if not (link := data.get("permalink")):
        return JsonResponse({"error": "Link is required."}, status=400)
    link_components = list(filter(None, link.split("/")))
    if link_components[-1] == settings.IMPRINT_SLUG:
        return imprint_page_feedback_internal(
            data, region, language, comment, rating, is_technical
        )
    data["slug"] = link_components[-1]
    if link_components[-2] == "events":
        return event_feedback_internal(
            data, region, language, comment, rating, is_technical
        )
    return page_feedback_internal(data, region, language, comment, rating, is_technical)
