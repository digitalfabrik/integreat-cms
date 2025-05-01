"""
This module includes functions related to the locations/POIs API endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import Prefetch
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags

from ...cms.constants import status
from ...cms.models import Contact, POICategoryTranslation
from ...cms.models.pois.poi import get_default_opening_hours
from ...core.utils.strtobool import strtobool
from ..decorators import json_response
from .location_categories import transform_location_category

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from ...cms.models import POI, POITranslation


def transform_poi(poi: POI | None) -> dict[str, Any]:
    """
    Function to create a JSON from a single poi object.

    :param poi: The poi object which should be converted
    :return: data necessary for API
    """
    if not poi:
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
        "id": poi.id,
        "name": poi.default_public_translation.title,
        "address": poi.address,
        "town": poi.city,
        "state": None,
        "postcode": poi.postcode,
        "region": None,
        "country": poi.country,
        "latitude": poi.latitude,
        "longitude": poi.longitude,
    }


def transform_poi_translation(poi_translation: POITranslation) -> dict[str, Any]:
    """
    Function to create a JSON from a single poi_translation object.

    :param poi_translation: The poi translation object which should be converted
    :return: data necessary for API
    """

    poi = poi_translation.poi

    contacts = Contact.objects.filter(location=poi).all()

    # Note(johannes): Remove the primary_contact and the according three fields (phone_number, website, and email) in late 2025
    # https://github.com/digitalfabrik/integreat-cms/issues/3475
    primary_contact = contacts.filter(area_of_responsibility="").first()

    contacts = contacts.filter(archived=False)

    contact_data = []
    for contact in contacts:
        contact_data.append(
            {
                "area_of_responsibility": contact.area_of_responsibility
                if contact.area_of_responsibility
                else None,
                "name": contact.name,
                "email": contact.email,
                "phone_number": contact.phone_number,
                "mobile_number": contact.mobile_phone_number,
                "website": contact.website,
            }
        )

    # Only return opening hours if they differ from the default value and the location is not temporarily closed
    opening_hours = None
    if not poi.temporarily_closed and poi.opening_hours != get_default_opening_hours():
        opening_hours = poi.opening_hours
    return {
        "id": poi_translation.id,
        "url": settings.BASE_URL + poi_translation.get_absolute_url(),
        "path": poi_translation.get_absolute_url(),
        "title": poi_translation.title,
        "modified_gmt": poi_translation.last_updated,  # deprecated field in the future
        "last_updated": timezone.localtime(poi_translation.last_updated),
        "meta_description": poi_translation.meta_description,
        "excerpt": strip_tags(poi_translation.content),
        "content": poi_translation.content,
        "available_languages": poi_translation.available_languages_dict,
        "icon": poi.icon.url if poi.icon else None,
        "thumbnail": poi.icon.thumbnail_url if poi.icon else None,
        "website": primary_contact.website if primary_contact else None,
        "email": primary_contact.email if primary_contact else None,
        "phone_number": primary_contact.phone_number if primary_contact else None,
        "contacts": contact_data,
        "category": transform_location_category(
            poi.category,
            poi_translation.language.slug,
        ),
        "temporarily_closed": poi.temporarily_closed,
        # Only return opening hours if not temporarily closed and they differ from the default value
        "opening_hours": opening_hours,
        "appointment_url": poi.appointment_url or None,
        "location": transform_poi(poi),
        "hash": None,
        "organization": (
            {
                "id": poi.organization.id,
                "slug": poi.organization.slug,
                "name": poi.organization.name,
                "logo": poi.organization.icon.url,
                "website": poi.organization.website,
            }
            if poi.organization
            else None
        ),
        "barrier_free": poi.barrier_free,
    }


@json_response
def locations(
    request: HttpRequest,
    language_slug: str,
    **kwargs: Any,
) -> JsonResponse:
    """
    List all POIs of the region and transform result into JSON

    :param request: The current request
    :param language_slug: The slug of the requested language
    :return: JSON object according to APIv3 locations endpoint definition
    """
    region = request.region
    # Throw a 404 error when the language does not exist or is disabled
    region.get_language_or_404(language_slug, only_active=True)
    result = []
    pois = (
        region.pois.prefetch_public_translations()
        .filter(
            archived=False,
            # Exclude locations without public translation in the default language
            translations__language=region.default_language,
            translations__status=status.PUBLIC,
        )
        .distinct()
        .select_related("category", "organization__icon")
        .prefetch_related(
            Prefetch(
                "category__translations",
                queryset=POICategoryTranslation.objects.select_related("language"),
            ),
        )
    )

    if "on_map" in request.GET:
        try:
            location_on_map = strtobool(request.GET["on_map"])
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        pois = pois.filter(location_on_map=location_on_map)

    for poi in pois:
        if translation := poi.get_public_translation(language_slug):
            result.append(transform_poi_translation(translation))

    return JsonResponse(
        result,
        safe=False,
    )  # Turn off Safe-Mode to allow serializing arrays
