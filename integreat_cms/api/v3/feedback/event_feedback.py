from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from django.http import Http404, JsonResponse

from ....cms.models import EventFeedback
from ...decorators import feedback_handler, json_response

if TYPE_CHECKING:
    from ....cms.models.languages.language import Language
    from ....cms.models.regions.region import Region

logger = logging.getLogger(__name__)


@feedback_handler
@json_response
def event_feedback(
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
    :return: decorated function that saves feedback in database
    """
    return event_feedback_internal(
        data, region, language, comment, rating, is_technical
    )


def event_feedback_internal(
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
    :raises ~django.http.Http404: HTTP status 404 if no event with the given slug exists.

    :return: JSON object according to APIv3 single page feedback endpoint definition
    """
    # Remove date from the slug for recurring events
    event_translation_slug = re.sub(r"\$\d{4}-\d{2}-\d{2}$", "", data.get("slug", ""))

    events = region.events.filter(
        translations__slug=event_translation_slug,
        translations__language=language,
    ).distinct()

    if len(events) > 1:
        logger.error(
            "Event translation slug %r is not unique per region and language, found multiple: %r",
            event_translation_slug,
            events,
        )
        return JsonResponse({"error": "Internal Server Error"}, status=500)

    event = None
    if len(events) == 1:
        event = events[0]
    elif region.fallback_translations_enabled:
        event = region.events.filter(
            translations__slug=event_translation_slug,
            translations__language=region.default_language,
        ).first()

    if not event:
        raise Http404("No matching event found for slug.")

    event_translation = event.get_translation(language.slug) or event.get_translation(
        region.default_language.slug
    )

    EventFeedback.objects.create(
        event_translation=event_translation,
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
