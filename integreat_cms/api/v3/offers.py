"""
This module includes functions related to the offers API endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse

from ...cms.constants import postal_code
from ..decorators import json_response

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from ...cms.models import OfferTemplate, Region


def get_url(offer: OfferTemplate, region: Region) -> str:
    """
    The offer should inherit the slug property from its template. This is the url to an API endpoint in most cases.
    Some offers depend on the location which is realized by adding the postal code of the current region to the
    request. If the offer template indicates that the postal code should be used as ``GET``-parameter, the class
    attribute ``use_postal_code`` has to be set to ``postal_code.GET`` (see :mod:`~integreat_cms.cms.constants.postal_code`) and
    the url has to end with the name of the required parameter-name, e.g. ``https://example.com/api?location=``.

    :param offer: one offer (formerly extra)
    :param region: current region object
    :return: The url of an offer
    """
    if offer.use_postal_code == postal_code.GET:
        return offer.url + region.postal_code
    return offer.url


def get_post_data(offer: OfferTemplate, region: Region) -> dict[str, str] | None:
    """
    In case the url expects additional post data, it is stored inside the ``post_data``-dict. Some offers depend on
    the location which is realized by adding the postal code of the current region to the request. If the offer
    template indicates that the postal code should be used as ``GET``-parameter, the class attribute
    ``use_postal_code`` has to be set to ``postal_code.POST`` (see :mod:`~integreat_cms.cms.constants.postal_code`) and then the
    key ``search-plz`` is automatically added to the post data. In case a third party service needs a different
    format, it has to be hard-coded here or we need other changes to the offer model.

    :param offer: one offer (formerly extra)
    :param region: current region object
    :return: The post data of the offer's url
    """
    post_data = offer.post_data
    if offer.use_postal_code == postal_code.POST:
        post_data.update({"search-plz": region.postal_code})
    if offer.is_zammad_form and region.zammad_url:
        post_data.update({"zammad-url": region.zammad_url})
    if not post_data:
        return None
    return post_data


def transform_offer(offer: OfferTemplate, region: Region) -> dict[str, Any]:
    """
    Function to create a JSON from a single offer Object.

    :param offer: one offer (formerly extra)
    :param region: current region object
    :return: data necessary for API
    """
    return {
        "name": offer.name,
        "alias": offer.slug,
        "url": get_url(offer, region),
        "post": get_post_data(offer, region),
        "thumbnail": offer.thumbnail,
    }


@json_response
# pylint: disable=unused-argument
def offers(
    request: HttpRequest, region_slug: str, language_slug: str | None = None
) -> JsonResponse:
    """
    Function to iterate through all offers related to a region and adds them to a JSON.

    :param request: Django request
    :param region_slug: slug of a region
    :param language_slug: language slug
    :return: JSON object according to APIv3 offers endpoint definition
    """
    region = request.region
    result = [transform_offer(offer, region) for offer in region.offers.all()]
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
