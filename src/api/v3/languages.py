"""
API-endpoint to deliver a JSON with all active languages of an region.
"""
from django.http import JsonResponse

from cms.models import Region


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
    region = Region.get_current_region(request)

    result = list(
        map(
            lambda l: {
                "id": l.language.id,
                "code": l.language.code,
                "native_name": l.language.native_name,
                "dir": l.language.text_direction,
            },
            region.language_tree_nodes.filter(active=True),
        )
    )
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
