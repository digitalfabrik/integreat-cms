"""
Provides an endpoint for delivering a JSON with all active extras.
"""
from django.http import JsonResponse

from cms.models import Region

def transform_extra(extra):
    """
    Function to create a JSON from a single extra Object.
    Returns:
        [String]: JSON-String with fields for the parameter of the extra
    """
    return {
        'name': extra.name,
        'alias': extra.slug,
        'url': extra.url,
        'post': extra.post_data,
        'thumbnail': extra.thumbnail
    }

#pylint: disable=unused-argument
def extras(request, region_slug, language_code=None):
    """
    Function to iterate through all extras related to a region and adds them to a JSON.

    Returns:
        [String]: [description]
    """
    region = Region.objects.get(slug=region_slug)
    result = []
    for extra in region.extras.all():
        result.append(transform_extra(extra))
    return JsonResponse(result, safe=False) # Turn off Safe-Mode to allow serializing arrays
