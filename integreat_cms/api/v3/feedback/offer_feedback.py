"""
APIv3 feedback endpoint for feedback about single offer
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

if TYPE_CHECKING:
    from ....cms.models import Language, Region

from ....cms.models import OfferFeedback
from ...decorators import feedback_handler, json_response


@feedback_handler
@json_response
def offer_feedback(
    data: dict[str, str],
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Store feedback about single offer in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :return: JSON object according to APIv3 offer feedback endpoint definition
    """
    offer = get_object_or_404(region.offers, slug=data.get("slug"))

    OfferFeedback.objects.create(
        offer=offer,
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
