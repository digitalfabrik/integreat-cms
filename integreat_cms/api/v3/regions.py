"""
This module includes functions related to the regions API endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import Http404, JsonResponse

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

from ...cms.constants import region_status
from ...cms.models import Region
from ..decorators import json_response
from .languages import transform_language


def transform_region(region: Region) -> dict[str, Any]:
    """
    Function to create a JSON from a single region object, including information if region is live/active.

    :param region: The region object which should be converted
    :return: data necessary for API
    """
    return {
        "id": region.id,
        "name": region.full_name,
        "path": region.slug,
        "live": region.status == region_status.ACTIVE,
        "prefix": region.prefix,
        "name_without_prefix": region.name,
        "plz": region.postal_code,
        "extras": region.offers.exists(),
        "events": region.events_enabled,
        "pois": region.locations_enabled,
        "push_notifications": region.push_notifications_enabled,
        "longitude": region.longitude,
        "latitude": region.latitude,
        "bounding_box": region.bounding_box.api_representation,
        "aliases": region.aliases,
        "tunews": region.external_news_enabled,
        "external_news": region.external_news_enabled,
        "languages": list(map(transform_language, region.visible_languages)),
        "is_chat_enabled": bool(
            region.integreat_chat_enabled
            and region.zammad_url
            and region.zammad_access_token
        ),
    }


@json_response
def regions(_: HttpRequest) -> JsonResponse:
    """
    List all regions that are not archived and transform result into JSON

    :return: JSON object according to APIv3 regions endpoint definition
    """
    result = list(
        map(transform_region, Region.objects.exclude(status=region_status.ARCHIVED))
    )
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays


@json_response
# pylint: disable=unused-argument
def region_by_slug(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Retrieve a single region and transform result into JSON

    :return: JSON object according to APIv3 live regions endpoint definition
    """
    if request.region.status == region_status.ARCHIVED:
        raise Http404("This region is archived.")

    return JsonResponse(
        transform_region(request.region), safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
