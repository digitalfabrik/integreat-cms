"""
Provides an endpoint for delivering a JSON with all active offers.
"""
from django.http import JsonResponse

from cms.models import Region


def transform_offer(offer):
    """
    Function to create a JSON from a single offer Object.
    Returns:
        [String]: JSON-String with fields for the parameter of the offer
    """
    return {
        "name": offer.name,
        "alias": offer.slug,
        "url": offer.url,
        "post": offer.post_data,
        "thumbnail": offer.thumbnail,
    }


# pylint: disable=unused-argument
def offers(request, region_slug, language_code=None):
    """
    Function to iterate through all offers related to a region and adds them to a JSON.

    Returns:
        [String]: [description]
    """
    region = Region.get_current_region(request)
    result = []
    for offer in region.offers.all():
        result.append(transform_offer(offer))
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
