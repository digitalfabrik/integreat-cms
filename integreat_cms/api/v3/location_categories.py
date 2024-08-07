"""
This module includes the POI category API endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.http import JsonResponse
from django.templatetags.static import static

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

from ...cms.models import POICategory
from ..decorators import json_response


def transform_location_category(
    location_category: POICategory, language_slug: str
) -> dict[str, Any] | None:
    """
    Function to create a JSON from a single location category object.

    :param location_category: The location category object which should be converted
    :param language_slug: The slug of the requested language
    :return: Data necessary for API
    """
    if not location_category:
        return None
    category_translation = location_category.get_translation(language_slug)
    return {
        "id": location_category.id,
        "name": (
            category_translation.name
            if category_translation
            else location_category.name
        ),
        "color": location_category.color,
        "icon": location_category.icon,
        "icon_url": (
            settings.BASE_URL
            + static(f"/svg/poi-category-icons/{location_category.icon}.svg")
        ),
        "icon_color": location_category.icon + "_" + location_category.color,
    }


@json_response
# pylint: disable=unused-argument
def location_categories(
    request: HttpRequest, region_slug: str, language_slug: str
) -> JsonResponse:
    """
    Function to return all POI categories as JSON.

    :param request: The current request
    :param region_slug: The slug of the requested region
    :param language_slug: The slug of the requested language
    :return: JSON object of all POI categories
    """
    region = request.region
    # Throw a 404 error when the language does not exist or is disabled
    region.get_language_or_404(language_slug, only_active=True)
    result = [
        transform_location_category(location_category, language_slug)
        for location_category in POICategory.objects.all()
    ]
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
