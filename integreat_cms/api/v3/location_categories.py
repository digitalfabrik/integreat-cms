"""
This module includes the POI category API endpoint.
"""
from django.http import JsonResponse

from ...cms.models import POICategory
from ..decorators import json_response


def transform_location_category(location_category, language_slug):
    """
    Function to create a JSON from a single location category object.

    :param location_category: The location category object which should be converted
    :type location_category: ~integreat_cms.cms.models.poi_categories.poi_category.POICategory

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: Data necessary for API
    :rtype: dict
    """
    if not location_category:
        return None
    category_translation = location_category.get_translation(language_slug)
    return {
        "id": location_category.id,
        "name": category_translation.name
        if category_translation
        else location_category.name,
        "color": location_category.color,
        "icon": location_category.icon,
    }


@json_response
# pylint: disable=unused-argument
def location_categories(request, region_slug, language_slug):
    """
    Function to return all POI categories as JSON.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the requested region
    :type region_slug: str

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: JSON object of all POI categories
    :rtype: ~django.http.JsonResponse
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
