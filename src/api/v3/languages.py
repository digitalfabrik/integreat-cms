"""
API-endpoint to deliver a JSON with all active languages of an region.
"""
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse

from cms.models import Region


def languages(request, region_slug):
    """
    Function to add all languages related to a region to a JSON.

    Args:
        request : Originally the request parameter, but is not used in this case.
        region_slug ([String]): Slug to identify the desired region.

    Returns:
        [String]: JSON with all used languages in a region.
    """
    try:
        region = Region.objects.get(slug=region_slug)

        result = list(
            map(
                lambda l: {
                    "id": l.language.id,
                    "code": l.language.code,
                    "native_name": l.language.name,
                    "dir": l.language.text_direction,
                },
                region.language_tree_nodes.filter(active=True),
            )
        )
        return JsonResponse(
            result, safe=False
        )  # Turn off Safe-Mode to allow serializing arrays
    except ObjectDoesNotExist:
        return HttpResponse(
            f'No Region found with name "{region_slug}".',
            content_type="text/plain",
            status=404,
        )
