"""
This module includes functions related to the event API endpoint.
"""

from datetime import datetime, timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags
from ..decorators import json_response
from .locations import transform_poi


def transform_event(event, custom_date=None):
    """
    Function to create a JSON from a single event object.

    :param event: The event which should be converted
    :type event: ~integreat_cms.cms.models.events.event.Event

    :param custom_date: The date overwrite of the event
    :type custom_date: ~datetime.date

    :return: data necessary for API
    :rtype: dict
    """
    start_local = event.start_local
    end_local = event.end_local
    if custom_date:
        start_local = datetime.combine(
            custom_date, start_local.time(), tzinfo=start_local.tzinfo
        )
        end_local = datetime.combine(
            custom_date + (end_local.date() - start_local.date()),
            end_local.time(),
            tzinfo=end_local.tzinfo,
        )

    return {
        "id": event.id if not custom_date else None,
        "start": start_local,
        "start_date": start_local.date(),  # deprecated field in the future
        "start_time": start_local.time(),  # deprecated field in the future
        "end": end_local,
        "end_date": end_local.date(),  # deprecated field in the future
        "end_time": end_local.time(),  # deprecated field in the future
        "all_day": event.is_all_day,
        "recurrence_id": event.recurrence_rule.id if event.recurrence_rule else None,
        "timezone": event.timezone,
    }


def transform_event_translation(event_translation, recurrence_date=None):
    """
    Function to create a JSON from a single event_translation object.

    :param event_translation: The event translation object which should be converted
    :type event_translation: ~integreat_cms.cms.models.events.event_translation.EventTranslation

    :param recurrence_date: The recurrence date for the event
    :type recurrence_date: ~datetime.date

    :return: data necessary for API
    :rtype: dict
    """
    event = event_translation.event
    slug = (
        event_translation.slug
        if not recurrence_date
        else f"{event_translation.slug}${recurrence_date}"
    )
    absolute_url = event_translation.url_prefix + slug + "/"
    return {
        "id": event_translation.id,
        "url": settings.BASE_URL + absolute_url,
        "path": absolute_url,
        "title": event_translation.title,
        "modified_gmt": event_translation.last_updated,  # deprecated field in the future
        "last_updated": timezone.localtime(event_translation.last_updated),
        "excerpt": strip_tags(event_translation.content),
        "content": event_translation.content,
        "available_languages": transform_available_languages(
            event_translation, recurrence_date
        )
        if recurrence_date
        else event_translation.available_languages_dict,
        "thumbnail": event.icon.url if event.icon else None,
        "location": transform_poi(event.location),
        "event": transform_event(event, recurrence_date),
        "hash": None,
    }


def transform_available_languages(event_translation, recurrence_date):
    """
    Function to create a JSON object of all available translations of an event translation.
    This is similar to `event_translation.available_languages_dict` embeds the recurrence date in the translation slug.

    :param event_translation: The event translation object which should be converted
    :type event_translation: ~integreat_cms.cms.models.events.event_translation.EventTranslation

    :param recurrence_date: The date of this event translation
    :type recurrence_date: ~datetime.date

    :return: data necessary for API
    :rtype: dict
    """
    languages = {}

    for translation in event_translation.foreign_object.available_translations():
        if translation.language == event_translation.language:
            continue

        slug = f"{translation.slug}${recurrence_date}"
        path = translation.url_prefix + slug + "/"
        languages[translation.language.slug] = {
            "id": None,
            "url": settings.BASE_URL + path,
            "path": path,
        }

    return languages


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

    start_date = event.start_local.date()
    event_translation.id = None

    # Calculate all recurrences of this event
    for recurrence_date in recurrence_rule.iter_after(start_date):
        if recurrence_date - max(start_date, today) > timedelta(
            days=settings.API_EVENTS_MAX_TIME_SPAN_DAYS
        ):
            break
        if recurrence_date < today or recurrence_date == start_date:
            continue

        yield transform_event_translation(event_translation, recurrence_date)


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
            if event.end_local.date() >= now:
                result.append(transform_event_translation(event_translation))

            for future_event in transform_event_recurrences(event_translation, now):
                result.append(future_event)

    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
