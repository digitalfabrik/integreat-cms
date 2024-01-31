"""
APIv3 endpoint for feedback about the imprint
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.http import Http404, JsonResponse

from ....cms.models.feedback.imprint_page_feedback import ImprintPageFeedback
from ...decorators import feedback_handler, json_response

if TYPE_CHECKING:
    from ....cms.models import Language, Region

logger = logging.getLogger(__name__)


@feedback_handler
@json_response
def imprint_page_feedback(
    data: dict,
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Store feedback about imprint in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :return: decorated function that saves feedback in database
    """
    return imprint_page_feedback_internal(
        data, region, language, comment, rating, is_technical
    )


# pylint: disable=unused-argument
def imprint_page_feedback_internal(
    data: dict,
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Store feedback about imprint in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :raises ~django.http.Http404: HTTP status 404 if the region has no imprint

    :return: JSON object according to APIv3 imprint feedback endpoint definition
    """
    if region.imprint and language in region.visible_languages:
        ImprintPageFeedback.objects.create(
            region=region,
            language=language,
            rating=rating,
            comment=comment,
            is_technical=is_technical,
        )
        return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
    # If the corresponding imprint does not exist, return a 404 error
    logger.info(
        "The imprint for region %r in the language %s does not exist and no feedback can be given.",
        region,
        language,
    )
    raise Http404(
        "The imprint does not exist in this region for the selected language."
    )
