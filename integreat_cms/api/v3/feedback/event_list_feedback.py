"""
APIv3 endpoint for the events (list)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse

if TYPE_CHECKING:
    from ....cms.models import Language, Region

from ....cms.models import EventListFeedback
from ...decorators import feedback_handler, json_response


@feedback_handler
@json_response
def event_list_feedback(
    data: dict,  # pylint: disable=unused-argument
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Store feedback on events list in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :return: JSON object according to APIv3 event list feedback endpoint definition
    """
    EventListFeedback.objects.create(
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
