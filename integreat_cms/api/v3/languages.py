"""
This module includes functions related to the languages API endpoint.
"""
from django.http import Http404, JsonResponse

from ...cms.constants import region_status
from ..decorators import json_response


def transform_language(language):
    """
    Function to create a JSON from a single language object.

    :param language: The language object which should be converted
    :type language: ~integreat_cms.cms.models.languages.language.Language

    :return: data necessary for API
    :rtype: dict
    """
    return {
        "id": language.id,
        "code": language.slug,
        "bcp47_tag": language.bcp47_tag,
        "native_name": language.native_name,
        "dir": language.text_direction,
    }


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
    if request.region.status == region_status.ARCHIVED:
        raise Http404("This region is archived.")

    return JsonResponse(
        list(map(transform_language, request.region.visible_languages)), safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
