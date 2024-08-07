"""
This module contains view actions for objects related to POIs.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ....api.decorators import json_response
from ....nominatim_api.nominatim_api_client import NominatimApiClient
from ...decorators import permission_required
from ...models import POI

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_poi")
def archive_poi(
    request: HttpRequest, poi_id: int, region_slug: str, language_slug: str
) -> HttpResponseRedirect:
    """
    Archive POI object

    :param request: The current request
    :param poi_id: The id of the POI which should be archived
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    """
    poi = POI.objects.get(id=poi_id)

    if poi.events.count() > 0:
        messages.error(
            request,
            _("This location cannot be archived because it is referenced by an event."),
        )
    else:
        poi.archive()
        logger.debug("%r archived by %r", poi, request.user)
        messages.success(request, _("Location was successfully archived"))

    return redirect(
        "pois",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.change_poi")
def restore_poi(
    request: HttpRequest, poi_id: int, region_slug: str, language_slug: str
) -> HttpResponseRedirect:
    """
    Restore POI object (set ``archived=False``)

    :param request: The current request
    :param poi_id: The id of the POI which should be restored
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    """
    poi = POI.objects.get(id=poi_id)

    poi.restore()

    logger.debug("%r restored by %r", poi, request.user)
    messages.success(request, _("Location was successfully restored"))

    return redirect(
        "pois",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.delete_poi")
def delete_poi(
    request: HttpRequest, poi_id: int, region_slug: str, language_slug: str
) -> HttpResponseRedirect:
    """
    Delete POI object

    :param request: The current request
    :param poi_id: The id of the POI which should be deleted
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    """

    poi = POI.objects.get(id=poi_id)
    logger.debug("%r deleted by %r", poi, request.user)
    poi.delete()
    messages.success(request, _("Location was successfully deleted"))

    return redirect(
        "pois",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@permission_required("cms.view_poi")
# pylint: disable=unused-argument
def view_poi(
    request: HttpRequest, poi_id: int, region_slug: str, language_slug: str
) -> HttpResponse:
    """
    View POI object

    :param request: The current request
    :param poi_id: The id of the POI which should be viewed
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :raises ~django.http.Http404: If user no translation exists for the requested POI and language

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    """
    poi = POI.objects.get(id=poi_id)

    if poi_translation := poi.get_translation(language_slug):
        # The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
        template_name = "pois/poi_view.html"
        return render(request, template_name, {"poi_translation": poi_translation})
    raise Http404


@json_response
@require_POST
@permission_required("cms.view_poi")
# pylint: disable=unused-argument
def auto_complete_address(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Autocomplete location address and coordinates

    :param request: The current request
    :param region_slug: The slug of the current region
    :raises ~django.http.Http404: If no location was found for the given address

    :return: The address and coordinates of the location
    """
    data = json.loads(request.body.decode("utf-8"))

    if not settings.NOMINATIM_API_ENABLED:
        return HttpResponse(_("Location service is disabled"), status_code=503)

    street_input = data.get("street")
    postcode_input = data.get("postcode")
    city_input = data.get("city")

    nominatim_api_client = NominatimApiClient()

    result = nominatim_api_client.search(
        street=street_input,
        postalcode=postcode_input,
        city=city_input,
        addressdetails=True,
    )

    if not result:
        raise Http404(_("Address could not be found"))

    address = result.raw.get("address", {})
    return JsonResponse(
        data={
            "postcode": address.get("postcode"),
            "city": address.get("city")
            or address.get("town")
            or address.get("village"),
            "country": address.get("country"),
            "longitude": result.longitude,
            "latitude": result.latitude,
        }
    )


@json_response
@require_POST
@permission_required("cms.view_poi")
# pylint: disable=unused-argument
def get_address_from_coordinates(
    request: HttpRequest, region_slug: str
) -> JsonResponse:
    """
    Derive address from the coordinates (map pin position)

    :param request: The current request
    :param region_slug: The slug of the current region
    :raises ~django.http.Http404: If no address was found for the given coordinates

    :return: The address of the location
    """
    if not settings.NOMINATIM_API_ENABLED:
        return HttpResponse(_("Location service is disabled"), status_code=503)

    data = json.loads(request.body.decode("utf-8"))

    nominatim_api_client = NominatimApiClient()

    result = nominatim_api_client.get_address(
        data.get("latitude"), data.get("longitude")
    )

    if not result:
        raise Http404(_("Address could not be found"))

    address = result.raw.get("address", {})

    return JsonResponse(
        data={
            "number": address.get("house_number"),
            "street": address.get("road"),
            "postcode": address.get("postcode"),
            "city": address.get("city")
            or address.get("town")
            or address.get("village"),
            "country": address.get("country"),
        }
    )
