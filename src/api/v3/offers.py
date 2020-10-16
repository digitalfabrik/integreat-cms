"""
Provides an endpoint for delivering a JSON with all active offers.
"""
from django.http import JsonResponse

from cms.models import Region


def transform_offer(offer):
    """
    Function to create a JSON from a single offer Object.

    :param offer: one offer (formerly extra)
    :type offer: ~cms.models.offers.offer.Offer

    :return: return data necessary for API
    :rtype: dict
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

    :param request: Django request
    :type request: ~django.http.HttpRequest
    :param region_slug: slug of a region
    :type region_slug: str
    :param language_code: language code
    :type language_code: str

    :return: JSON object according to APIv3 offers endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)
    result = []
    for offer in region.offers.all():
        result.append(transform_offer(offer))
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
