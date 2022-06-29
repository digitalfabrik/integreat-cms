"""
This module includes functions related to the event API endpoint.
"""

from copy import deepcopy

from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags

from ...cms.models.events.event_translation import EventTranslation
from ...cms.utils.slug_utils import generate_unique_slug
from ..decorators import json_response
from .locations import transform_poi


def transform_event(event):
    """
    Function to create a JSON from a single event object.

    :param event: The event which should be converted
    :type event: ~integreat_cms.cms.models.events.event.Event

    :return: data necessary for API
    :rtype: dict
    """
    return {
        "id": event.id,
        "start_date": event.start_date,
        "end_date": event.end_date,
        "all_day": event.is_all_day,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "recurrence_id": event.recurrence_rule.id if event.recurrence_rule else None,
        "timezone": settings.CURRENT_TIME_ZONE,
    }


def transform_event_translation(event_translation):
    """
    Function to create a JSON from a single event_translation object.

    :param event_translation: The event translation object which should be converted
    :type event_translation: ~integreat_cms.cms.models.events.event_translation.EventTranslation

    :return: data necessary for API
    :rtype: dict
    """
    event = event_translation.event
    absolute_url = event_translation.get_absolute_url()
    return {
        "id": event_translation.id,
        "url": settings.BASE_URL + absolute_url,
        "path": absolute_url,
        "title": event_translation.title,
        "modified_gmt": event_translation.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        "excerpt": strip_tags(event_translation.content),
        "content": event_translation.content,
        "available_languages": event_translation.available_languages,
        "thumbnail": event.icon.url if event.icon else None,
        "location": transform_poi(event.location),
        "event": transform_event(event),
        "hash": None,
    }


def transform_event_recurrences(event_translation, today):
    """
    Yield all future recurrences of the event.

    :param event_translation: The event translation object which should be converted
    :type event_translation: ~integreat_cms.cms.models.events.event_translation.EventTranslation

    :param today: The first date at which event may be yielded
    :type today: ~datetime.date

    :return: An iterator over all future recurrences up to ``settings.API_EVENTS_MAX_TIME_SPAN_DAYS``
    :rtype: Iterator[:class:`~datetime.date`]
    """
    event = event_translation.event
    recurrence_rule = event.recurrence_rule
    if not recurrence_rule:
        return

    # In order to avoid unnecessary computations, check if any future event
    # may be valid and return early if that is not the case
    if (
        recurrence_rule.recurrence_end_date
        and recurrence_rule.recurrence_end_date < today
    ):
        return

    event_length = event.end_date - event.start_date
    start_date = event.start_date
    event_translation.id = None
    # Store language and slug for usage in loop
    current_language = event_translation.language
    current_slug = event_translation.slug
    # Calculate all recurrences of this event
    for recurrence_date in recurrence_rule.iter_after(start_date):
        if recurrence_date - max(start_date, today) > timedelta(
            days=settings.API_EVENTS_MAX_TIME_SPAN_DAYS
        ):
            break
        if recurrence_date < today or recurrence_date == start_date:
            continue
        # Create all temporary translations of this recurrence
        recurrence_translations = {}
        if event.region.fallback_translations_enabled:
            languages = event.region.active_languages
        else:
            languages = event.public_languages
        for language in languages:
            # Create copy in memory to make sure original translation is not affected by changes
            event_translation = deepcopy(event_translation)
            # Fake the requested language
            event_translation.language = language
            event_translation.slug = generate_unique_slug(
                **{
                    "slug": f"{current_slug}-{recurrence_date}",
                    "manager": EventTranslation.objects,
                    "object_instance": event_translation,
                    "foreign_model": "event",
                    "region": event.region,
                    "language": language,
                }
            )
            # Reset id to make sure id does not conflict with existing event translation
            event_translation.event.id = None
            # Set date to recurrence date
            event_translation.event.start_date = recurrence_date
            event_translation.event.end_date = recurrence_date + event_length
            # Clear cached property in case url with different language was already calculated before
            try:
                del event_translation.url_prefix
            except AttributeError:
                pass
            recurrence_translations[language.slug] = event_translation

        # Set the prefetched public translations to make sure the recurrence translations are correctly listed in available languages
        for recurrence_translation in recurrence_translations.values():
            recurrence_translation.event.prefetched_public_translations_by_language_slug = (
                recurrence_translations
            )
        # Update translation object with the one with prefetched temporary translations
        event_translation = recurrence_translations[current_language.slug]
        # Clear cached property in case available languages with different recurrence was already calculated before
        try:
            del event_translation.available_languages
        except AttributeError:
            pass
        yield transform_event_translation(event_translation)


@json_response
# pylint: disable=unused-argument
def events(request, region_slug, language_slug):
    """
    List all events of the region and transform result into JSON

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the requested region
    :type region_slug: str

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: JSON object according to APIv3 events endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    region = request.region
    # Throw a 404 error when the language does not exist or is disabled
    region.get_language_or_404(language_slug, only_active=True)
    result = []
    now = timezone.now().date()
    for event in region.events.prefetch_public_translations().filter(archived=False):
        event_translation = event.get_public_translation(language_slug)
        if event_translation:
            if event.end_date >= now:
                result.append(transform_event_translation(event_translation))

            for future_event in transform_event_recurrences(event_translation, now):
                result.append(future_event)

    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
