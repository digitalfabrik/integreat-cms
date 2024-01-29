"""
APIv3 endpoint for feedback about full region (main level of content)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse

from ....cms.models import RegionFeedback
from ...decorators import feedback_handler, json_response

if TYPE_CHECKING:
    from ....cms.models import Language, Region


@feedback_handler
@json_response
# pylint: disable=unused-argument
def region_feedback(
    data: dict,
    region: Region,
    language: Language,
    comment: str,
    rating: bool | None,
    is_technical: bool,
) -> JsonResponse:
    """
    Store feedback about region / main pages in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :return: JSON object according to APIv3 region feedback endpoint definition
    """
    RegionFeedback.objects.create(
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
