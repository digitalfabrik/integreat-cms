"""
This module contains view actions for objects related to POIs.
"""
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from ....api.decorators import json_response
from ...decorators import permission_required
from ...models import POI

from ....nominatim_api.nominatim_api_client import NominatimApiClient

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_poi")
def archive_poi(request, poi_id, region_slug, language_slug):
    """
    Archive POI object

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param poi_id: The id of the POI which should be archived
    :type poi_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    poi = POI.objects.get(id=poi_id)

    poi.archive()

    logger.debug("%r archived by %r", poi, request.user)
    messages.success(request, _("Location was successfully archived"))

    return redirect(
        "pois",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        }
    )


@require_POST
@permission_required("cms.change_poi")
def restore_poi(request, poi_id, region_slug, language_slug):
    """
    Restore POI object (set ``archived=False``)

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param poi_id: The id of the POI which should be restored
    :type poi_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    :rtype: ~django.http.HttpResponseRedirect
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
        }
    )


@require_POST
@permission_required("cms.delete_poi")
def delete_poi(request, poi_id, region_slug, language_slug):
    """
    Delete POI object

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param poi_id: The id of the POI which should be deleted
    :type poi_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    :rtype: ~django.http.HttpResponseRedirect
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
        }
    )


@permission_required("cms.view_poi")
# pylint: disable=unused-argument
def view_poi(request, poi_id, region_slug, language_slug):
    """
    View POI object

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param poi_id: The id of the POI which should be viewed
    :type poi_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.http.Http404: If user no translation exists for the requested POI and language

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pois/poi_view.html"
    poi = POI.objects.get(id=poi_id)

    poi_translation = poi.get_translation(language_slug)

    if not poi_translation:
        raise Http404

    return render(request, template_name, {"poi_translation": poi_translation})


@json_response
@require_POST
@permission_required("cms.view_poi")
# pylint: disable=unused-argument
def auto_complete_address(request, region_slug):
    """
    Autocomplete location address and coordinates

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.http.Http404: If no location was found for the given address

    :return: The address and coordinates of the location
    :rtype: ~django.http.JsonResponse
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
def get_address_from_coordinates(request, region_slug):
    """
    Derive address from the coordinates (map pin position)

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.http.Http404: If no address was found for the given coordinates

    :return: The address of the location
    :rtype: ~django.http.JsonResponse
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
