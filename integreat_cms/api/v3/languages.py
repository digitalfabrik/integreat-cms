"""
This module includes functions related to the languages API endpoint.
"""
from django.http import JsonResponse

from ..decorators import json_response


@json_response
# pylint: disable=unused-argument
def languages(request, region_slug):
    """
    Function to add all languages related to a region to a JSON.

    :param request: Django request
    :type request: ~django.http.HttpRequest
    :param region_slug: slug of a region
    :type region_slug: str

    :return: JSON object according to APIv3 languages endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    result = [
        {
            "id": language.id,
            "code": language.slug,
            "bcp47_tag": language.bcp47_tag,
            "native_name": language.native_name,
            "dir": language.text_direction,
        }
        for language in region.visible_languages
    ]
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
