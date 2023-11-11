from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.http import Http404, JsonResponse

from ....cms.models import POIFeedback
from ...decorators import feedback_handler, json_response

if TYPE_CHECKING:
    from ....cms.models import Language, Region

logger = logging.getLogger(__name__)


@feedback_handler
@json_response
def poi_feedback(
    data: dict[str, str],
    region: Region,
    language: Language,
    comment: str,
    rating: bool,
    is_technical: bool,
) -> JsonResponse:
    """
    Store feedback about single POI in database

    :param data: HTTP request body data
    :param region: The region of this sitemap's urls
    :param language: The language of this sitemap's urls
    :param comment: The comment sent as feedback
    :param rating: up or downvote, neutral
    :param is_technical: is feedback on content or on tech
    :raises ~django.http.Http404: HTTP status 404 if no POI with the given slug exists.

    :return: decorated function that saves feedback in database
    """
    poi_translation_slug = data.get("slug")

    pois = region.pois.filter(
        translations__slug=data.get("slug"),
        translations__language=language,
    ).distinct()

    if len(pois) > 1:
        logger.error(
            "POI translation slug %r is not unique per region and language, found multiple: %r",
            poi_translation_slug,
            pois,
        )
        return JsonResponse({"error": "Internal Server Error"}, status=500)

    poi = None
    if len(pois) == 1:
        poi = pois[0]
    elif region.fallback_translations_enabled:
        poi = region.pois.filter(
            translations__slug=data.get("slug"),
            translations__language=region.default_language,
        ).first()

    if not poi:
        raise Http404("No matching location found for slug.")

    poi_translation = poi.get_translation(language.slug) or poi.get_translation(
        region.default_language.slug
    )

    POIFeedback.objects.create(
        poi_translation=poi_translation,
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
