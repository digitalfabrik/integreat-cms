"""
This module includes the place category API endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.http import JsonResponse
from django.templatetags.static import static

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

from ...cms.models import PlaceCategory
from ..decorators import json_response


def transform_place_category(
    place_category: PlaceCategory,
    language_slug: str,
) -> dict[str, Any] | None:
    """
    Function to create a JSON from a single place category object.

    :param place_category: The place category object which should be converted
    :param language_slug: The slug of the requested language
    :return: Data necessary for API
    """
    if not place_category:
        return None
    category_translation = place_category.get_translation(language_slug)
    return {
        "id": place_category.id,
        "name": (
            category_translation.name if category_translation else place_category.name
        ),
        "color": place_category.color,
        "icon": place_category.icon,
        "icon_url": (
            settings.BASE_URL
            + static(f"/svg/poi-category-icons/{place_category.icon}.svg")
        ),
        "icon_color": place_category.icon + "_" + place_category.color,
    }


@json_response
def place_categories(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
) -> JsonResponse:
    """
    Function to return all place categories as JSON.

    :param request: The current request
    :param language_slug: The slug of the requested language
    :return: JSON object of all place categories
    """
    region = request.region
    # Throw a 404 error when the language does not exist or is disabled
    region.get_language_or_404(language_slug, only_active=True)
    result = [
        transform_place_category(place_category, language_slug)
        for place_category in PlaceCategory.objects.all()
    ]
    return JsonResponse(
        result,
        safe=False,
    )  # Turn off Safe-Mode to allow serializing arrays
