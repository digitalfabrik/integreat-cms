"""
This module includes functions related to the event API endpoint.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags

from ..decorators import json_response
from .locations import transform_poi

if TYPE_CHECKING:
    from datetime import date
    from typing import Any, Iterator

    from django.http import HttpRequest

    from ...cms.models import Event, EventTranslation, POITranslation


def transform_event(event: Event, custom_date: date | None = None) -> dict[str, Any]:
    """
    Function to create a JSON from a single event object.

    :param event: The event which should be converted
    :param custom_date: The date overwrite of the event
    :return: data necessary for API
    """
    start_local = event.start_local
    end_local = event.end_local
    if custom_date:
        end_local = datetime.combine(
            custom_date + (end_local.date() - start_local.date()),
            end_local.time(),
            tzinfo=end_local.tzinfo,
        )
        start_local = datetime.combine(
            custom_date, start_local.time(), tzinfo=start_local.tzinfo
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


def transform_event_translation(
    event_translation: EventTranslation,
    poi_translation: POITranslation | None,
    recurrence_date: date | None = None,
) -> dict[str, Any]:
    """
    Function to create a JSON from a single event_translation object.

    :param event_translation: The event translation object which should be converted
    :param poi_translation: The poi translation object which is associated to this event
    :param recurrence_date: The recurrence date for the event
    :return: data necessary for API
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
        "available_languages": (
            transform_available_languages(event_translation, recurrence_date)
            if recurrence_date
            else event_translation.available_languages_dict
        ),
        "thumbnail": event.icon.url if event.icon else None,
        "location": transform_poi(event.location),
        "location_path": (
            poi_translation.get_absolute_url() if poi_translation else None
        ),
        "event": transform_event(event, recurrence_date),
        "hash": None,
        "recurrence_rule": (
            event.recurrence_rule.to_ical_rrule_string()
            if event.recurrence_rule
            else None
        ),
    }


def transform_available_languages(
    event_translation: EventTranslation, recurrence_date: date
) -> dict[str, dict[str, str | None]]:
    """
    Function to create a JSON object of all available translations of an event translation.
    This is similar to `event_translation.available_languages_dict` embeds the recurrence date in the translation slug.

    :param event_translation: The event translation object which should be converted
    :param recurrence_date: The date of this event translation
    :return: data necessary for API
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


def transform_event_recurrences(
    event_translation: EventTranslation,
    poi_translation: POITranslation | None,
    today: date,
) -> Iterator[dict[str, Any]]:
    """
    Yield all future recurrences of the event.

    :param event_translation: The event translation object which should be converted
    :param poi_translation: The poi translation object which is associated to this event
    :param today: The first date at which event may be yielded
    :return: An iterator over all future recurrences up to ``settings.API_EVENTS_MAX_TIME_SPAN_DAYS``
    """

    event = event_translation.event

    if not event.recurrence_rule or (
        event.recurrence_rule.recurrence_end_date
        and event.recurrence_rule.recurrence_end_date < today
    ):
        return

    start_date = event.start_local.date()
    event_translation.id = None

    # Calculate all recurrences of this event
    for recurrence_date in event.recurrence_rule.iter_after(start_date):
        if recurrence_date - max(start_date, today) > timedelta(
            days=settings.API_EVENTS_MAX_TIME_SPAN_DAYS
        ):
            break
        if recurrence_date < today:
            continue

        yield transform_event_translation(
            event_translation, poi_translation, recurrence_date
        )


@json_response
# pylint: disable=unused-argument
def events(request: HttpRequest, region_slug: str, language_slug: str) -> JsonResponse:
    """
    List all events of the region and transform result into JSON

    :param request: The current request
    :param region_slug: The slug of the requested region
    :param language_slug: The slug of the requested language
    :return: JSON object according to APIv3 events endpoint definition
    """
    region = request.region
    # Throw a 404 error when the language does not exist or is disabled
    region.get_language_or_404(language_slug, only_active=True)

    result: list[dict[str, str | int | None]] = []
    now = timezone.now().date()
    combine_recurring_events = "combine_recurring" in request.GET
    for event in region.events.prefetch_public_translations().filter(archived=False):
        if not event.is_past and (
            event_translation := event.get_public_translation(language_slug)
        ):
            poi_translation = (
                event.location.get_public_translation(language_slug)
                if event_translation.event.location
                else None
            )
            if event.is_recurring and not combine_recurring_events:
                result.extend(
                    iter(
                        transform_event_recurrences(
                            event_translation, poi_translation, now
                        )
                    )
                )
            else:
                result.append(
                    transform_event_translation(event_translation, poi_translation)
                )

    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
