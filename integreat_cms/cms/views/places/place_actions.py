"""
This module contains view actions for objects related to places.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ....api.decorators import json_response
from ....nominatim_api.nominatim_api_client import NominatimApiClient
from ...decorators import permission_required
from ...models import Place

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_place")
def archive_place(
    request: HttpRequest,
    place_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Archive place object

    :param request: The current request
    :param place_id: The id of the place which should be archived
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: A redirection to the :class:`~integreat_cms.cms.views.places.place_list_view.PlaceListView`
    """
    place = Place.objects.get(id=place_id)

    if place.archive():
        logger.debug("%r archived by %r", place, request.user)
        messages.success(request, _("Place was successfully archived"))
    else:
        messages.error(
            request,
            _(
                "This place cannot be archived because it is referenced by an event or a contact that is not archived."
            ),
        )

    return redirect(
        "places",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.change_place")
def restore_place(
    request: HttpRequest,
    place_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Restore place object (set ``archived=False``)

    :param request: The current request
    :param place_id: The id of the place which should be restored
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: A redirection to the :class:`~integreat_cms.cms.views.places.place_list_view.PlaceListView`
    """
    place = Place.objects.get(id=place_id)

    place.restore()

    logger.debug("%r restored by %r", place, request.user)
    messages.success(request, _("Place was successfully restored"))

    return redirect(
        "places",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.delete_place")
def delete_place(
    request: HttpRequest,
    place_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Delete place object

    :param request: The current request
    :param place_id: The id of the place which should be deleted
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: A redirection to the :class:`~integreat_cms.cms.views.places.place_list_view.PlaceListView`
    """

    place = Place.objects.get(id=place_id)
    can_delete, error_msg = place.can_be_deleted()
    if can_delete:
        if not place.region.contacts_enabled:
            # Delete all related contacts if the contact module is deactivated in the region,
            # as users cannot edit or delete contact objects.
            # Otherwise place cannot be deleted by things users cannot delete.
            place.contacts.all().delete()
        place.delete()
        logger.info("%r deleted by %r", place, request.user)
        messages.success(request, _("Place was successfully deleted"))
    else:
        logger.info("%r couldn't be deleted by %r", place, request.user)
        messages.error(
            request,
            _("Place couldn't be deleted, because {failure_reason}").format(
                failure_reason=error_msg
            ),
        )

    return redirect(
        "places",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@permission_required("cms.view_place")
def view_place(
    request: HttpRequest,
    place_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponse:
    """
    View place object

    :param request: The current request
    :param place_id: The id of the place which should be viewed
    :param language_slug: The slug of the current language
    :raises ~django.http.Http404: If user no translation exists for the requested place and language

    :return: A redirection to the :class:`~integreat_cms.cms.views.places.place_list_view.PlaceListView`
    """
    place = Place.objects.get(id=place_id)

    if place_translation := place.get_translation(language_slug):
        # The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
        template_name = "places/place_view.html"
        return render(request, template_name, {"place_translation": place_translation})
    raise Http404


@require_POST
@permission_required("cms.change_place")
def copy_place(
    request: HttpRequest,
    place_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Duplicates the given event and all of its translations.

    :param request: Object representing the user call
    :param place_id: internal id of the place to be copied
    :param region_slug: slug of the region which the event belongs to
    :param language_slug: current GUI language slug
    :return: The rendered template response
    """
    region = request.region
    place = get_object_or_404(region.places, id=place_id)

    place.copy(request.user)

    logger.debug("%r copied by %r", place, request.user)
    messages.success(request, _("Place was successfully copied"))

    return redirect(
        "places",
        **{"region_slug": region_slug, "language_slug": language_slug},
    )


@json_response
@require_POST
@permission_required("cms.view_place")
def auto_complete_address(
    request: HttpRequest,
    region_slug: str,
) -> JsonResponse:
    """
    Autocomplete place address and coordinates

    :param request: The current request
    :raises ~django.http.Http404: If no place was found for the given address

    :return: The address and coordinates of the place
    """
    data = json.loads(request.body.decode("utf-8"))

    if not settings.NOMINATIM_API_ENABLED:
        return HttpResponse(_("Place service is disabled"), status_code=503)

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
        raise Http404(_("Coordinates could not be found"))

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
        },
    )


@json_response
@require_POST
@permission_required("cms.view_place")
def get_address_from_coordinates(
    request: HttpRequest,
    region_slug: str,
) -> JsonResponse:
    """
    Derive address from the coordinates (map pin position)

    :param request: The current request
    :raises ~django.http.Http404: If no address was found for the given coordinates

    :return: The address of the place
    """
    if not settings.NOMINATIM_API_ENABLED:
        return HttpResponse(_("Place service is disabled"), status_code=503)

    data = json.loads(request.body.decode("utf-8"))

    nominatim_api_client = NominatimApiClient()

    result = nominatim_api_client.get_address(
        data.get("latitude"),
        data.get("longitude"),
    )

    if not result:
        raise Http404(_("Coordinates could not be found"))

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
        },
    )
