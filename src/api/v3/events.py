from django.http import JsonResponse
from django.utils import timezone

from backend.settings import WEBAPP_URL, CURRENT_TIME_ZONE
from cms.models import Region
from .locations import transform_poi
from ..decorators import json_response


def transform_event(event):
    """
    Function to create a JSON from a single event object.

    :param event: The event which should be converted
    :type event: ~cms.models.events.event.Event

    :return: return data necessary for API
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
        "timezone": CURRENT_TIME_ZONE,
    }


def transform_event_translation(event_translation):
    """
    Function to create a JSON from a single event_translation object.

    :param event_translation: The event translation object which should be converted
    :type event_translation: ~cms.models.events.event_translation.EventTranslation

    :return: return data necessary for API
    :rtype: dict
    """

    event = event_translation.event
    if event.location:
        location_translation = (
            event.location.get_public_translation(event_translation.language.slug)
            or event.location.default_translation
        )
        location = transform_poi(event.location, location_translation)
    else:
        location = None

    return {
        "id": event_translation.id,
        "url": WEBAPP_URL + event_translation.get_absolute_url(),
        "path": event_translation.get_absolute_url(),
        "title": event_translation.title,
        "modified_gmt": event_translation.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        "excerpt": event_translation.description,
        "content": event_translation.description,
        "available_languages": event_translation.available_languages,
        "thumbnail": event.icon.url if event.icon else None,
        "location": location,
        "event": transform_event(event),
        "hash": None,
    }


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
    region = Region.get_current_region(request)
    result = []
    for event in region.events.filter(archived=False, end_date__gte=timezone.now()):
        event_translation = event.get_public_translation(language_slug)
        if event_translation:
            result.append(transform_event_translation(event_translation))

    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
