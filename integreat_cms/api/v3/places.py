"""
This module includes functions related to the places API endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import Prefetch
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags

from ...cms.constants import status
from ...cms.models import Contact, PlaceCategoryTranslation
from ...cms.models.places.place import get_default_opening_hours
from ...core.utils.strtobool import strtobool
from ..decorators import json_response
from .place_categories import transform_place_category

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from ...cms.models import Place, PlaceTranslation

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _ensure_zoneinfo(tz_candidate: str | ZoneInfo | None) -> ZoneInfo:
    """
    Convert an optional string/ZoneInfo to a valid :class:`ZoneInfo`, defaulting to settings.TIME_ZONE.

    :param tz_candidate: IANA zone string, ZoneInfo, or None.
    :return: Validated ZoneInfo.
    """
    default_tz = getattr(settings, "TIME_ZONE", "Europe/Berlin")
    if isinstance(tz_candidate, ZoneInfo):
        return tz_candidate
    if isinstance(tz_candidate, str):
        tz_str = tz_candidate.strip()
        if tz_str:
            try:
                return ZoneInfo(tz_str)
            except ZoneInfoNotFoundError:
                pass
    return ZoneInfo(default_tz)


def transform_place(place: Place | None) -> dict[str, Any]:
    """
    Function to create a JSON from a single place object.

    :param place: The place object which should be converted
    :return: data necessary for API
    """
    if not place:
        return {
            "id": None,
            "name": None,
            "address": None,
            "town": None,
            "state": None,
            "postcode": None,
            "region": None,
            "country": None,
            "latitude": None,
            "longitude": None,
        }
    return {
        "id": place.id,
        "name": (
            place.default_public_translation.title
            if place.default_public_translation
            else None
        ),
        "address": place.address,
        "town": place.city,
        "state": None,
        "postcode": place.postcode,
        "region": None,
        "country": place.country,
        "latitude": place.latitude,
        "longitude": place.longitude,
    }


def transform_opening_hours(
    region_tz: ZoneInfo, opening_hours: list
) -> list[dict[str, Any]]:
    tz_key = getattr(region_tz, "key", str(region_tz))
    return [
        day
        | {
            "timeSlots": [
                (slot | {"timezone": tz_key}) for slot in day.get("timeSlots", [])
            ]
        }
        for day in (opening_hours or [])
    ]


def transform_place_translation(
    place_translation: PlaceTranslation,
    *,
    region_tz: ZoneInfo,
) -> dict[str, Any]:
    """
    Create JSON for a place translation and enrich opening hours with ISO-8601 times.


    :param place_translation: Place translation to convert.
    :param region_tz: Validated time zone used to compute DST-aware numeric offsets.
    :return: Data for the APIv3 locations endpoint.
    """
    place = place_translation.place

    contacts = Contact.objects.filter(place=place).all()

    # Note(johannes): Remove the primary_contact and the according three fields (phone_number, website, and email) in late 2025
    # https://github.com/digitalfabrik/integreat-cms/issues/3475
    primary_contact = contacts.get_primary_contact()

    contacts = contacts.filter(archived=False)

    contact_data = []
    for contact in contacts:
        contact_opening_hours = (
            transform_opening_hours(
                region_tz=region_tz, opening_hours=contact.opening_hours
            )
            if contact.opening_hours != get_default_opening_hours()
            else None
        )
        contact_data.append(
            {
                "area_of_responsibility": contact.area_of_responsibility or None,
                "name": contact.name,
                "email": contact.email,
                "phone_number": contact.phone_number,
                "mobile_number": contact.mobile_phone_number,
                "website": contact.website,
                "opening_hours": contact_opening_hours,
                "appointment_url": contact.appointment_url or None,
            }
        )
    place_opening_hours = (
        transform_opening_hours(region_tz=region_tz, opening_hours=place.opening_hours)
        if not place.temporarily_closed
        and place.opening_hours != get_default_opening_hours()
        else None
    )

    return {
        "id": place_translation.id,
        "url": settings.BASE_URL + place_translation.get_absolute_url(),
        "path": place_translation.get_absolute_url(),
        "title": place_translation.title,
        "modified_gmt": place_translation.last_updated,  # deprecated field in the future
        "last_updated": timezone.localtime(place_translation.last_updated),
        "published_at": timezone.localtime(
            place_translation.published_at or place_translation.last_updated,
        ),
        "meta_description": place_translation.meta_description,
        "excerpt": strip_tags(place_translation.content),
        "content": place_translation.content,
        "available_languages": place_translation.available_languages_dict,
        "icon": place.icon.url if place.icon else None,
        "thumbnail": place.icon.thumbnail_url if place.icon else None,
        "website": primary_contact.website if primary_contact else None,
        "email": primary_contact.email if primary_contact else None,
        "phone_number": primary_contact.phone_number if primary_contact else None,
        "contacts": contact_data,
        "category": transform_place_category(
            place.category,
            place_translation.language.slug,
        ),
        "temporarily_closed": place.temporarily_closed,
        # Only return opening hours if not temporarily closed and they differ from the default value
        "opening_hours": place_opening_hours,
        "appointment_url": place.appointment_url or None,
        "location": transform_place(place),
        "hash": None,
        "organization": (
            {
                "id": place.organization.id,
                "slug": place.organization.slug,
                "name": place.organization.name,
                "logo": place.organization.icon.url,
                "website": place.organization.website,
            }
            if place.organization
            else None
        ),
        "barrier_free": place.barrier_free,
    }


@json_response
def places(
    request: HttpRequest,
    language_slug: str,
    **kwargs: Any,
) -> JsonResponse:
    """
    List all places of the region and transform result into JSON

    :param request: The current request
    :param language_slug: The slug of the requested language
    :return: JSON object according to APIv3 locations endpoint definition
    """
    region = request.region
    # Throw a 404 error when the language does not exist or is disabled
    region.get_language_or_404(language_slug, only_active=True)
    result = []
    places = (
        region.places.prefetch_public_translations()
        .filter(
            archived=False,
            # Exclude places without public translation in the default language
            translations__language=region.default_language,
            translations__status=status.PUBLIC,
        )
        .distinct()
        .select_related("category", "organization__icon")
        .prefetch_related(
            Prefetch(
                "category__translations",
                queryset=PlaceCategoryTranslation.objects.select_related("language"),
            ),
        )
    )

    if "on_map" in request.GET:
        try:
            place_on_map = strtobool(request.GET["on_map"])
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        places = places.filter(place_on_map=place_on_map)

    region_tz = _ensure_zoneinfo(getattr(region, "timezone", None))
    for place in places:
        if translation := place.get_public_translation(language_slug):
            result.append(transform_place_translation(translation, region_tz=region_tz))

    return JsonResponse(
        result,
        safe=False,
    )  # Turn off Safe-Mode to allow serializing arrays
