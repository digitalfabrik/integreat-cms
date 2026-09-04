from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.http import Http404, JsonResponse

from ....cms.models import PlaceFeedback
from ...decorators import feedback_handler, json_response

if TYPE_CHECKING:
    from ....cms.models import Language, Region

logger = logging.getLogger(__name__)


@feedback_handler
@json_response
def place_feedback(
    data: dict[str, str],
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Store feedback about single Place in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :raises ~django.http.Http404: HTTP status 404 if no Place with the given slug exists.

    :return: decorated function that saves feedback in database
    """
    place_translation_slug = data.get("slug")

    places = region.places.filter(
        translations__slug=data.get("slug"),
        translations__language=language,
    ).distinct()

    if len(places) > 1:
        logger.error(
            "Place translation slug %r is not unique per region and language, found multiple: %r",
            place_translation_slug,
            places,
        )
        return JsonResponse({"error": "Internal Server Error"}, status=500)

    place = None
    if len(places) == 1:
        place = places[0]
    elif region.fallback_translations_enabled:
        place = region.places.filter(
            translations__slug=data.get("slug"),
            translations__language=region.default_language,
        ).first()

    if not place:
        raise Http404("No matching place found for slug.")

    place_translation = place.get_translation(language.slug) or place.get_translation(
        region.default_language.slug,
    )

    PlaceFeedback.objects.create(
        place_translation=place_translation,
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
