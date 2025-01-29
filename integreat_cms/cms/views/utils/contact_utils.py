from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...models import Contact

if TYPE_CHECKING:
    from django.http import HttpRequest


logger = logging.getLogger(__name__)

MAX_RESULT_COUNT: int = 20


@require_POST
def search_contact_ajax(
    request: HttpRequest,
    region_slug: str | None = None,
) -> JsonResponse:
    """
    Searches contacts that match the search query.

    :param request: The current request
    :param region_slug: The slug of the current region
    :raises ~django.core.exceptions.PermissionDenied: If the user has no permission to the object type
    :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}
    """

    body = json.loads(request.body.decode("utf-8"))
    if (query := body["query_string"]) is None:
        return JsonResponse({"data": []})

    logger.debug("Ajax call: Live search for contact with query %r", query)

    if not request.user.has_perm("cms.view_contact"):
        raise PermissionDenied
    if request.region is None:
        raise ValueError("Expected a region to be provided")

    results = Contact.search(request.region, query)[:MAX_RESULT_COUNT]
    return JsonResponse(
        {
            "data": [
                {
                    "url": result.absolute_url,
                    "name": result.get_repr_short,
                    "details": result.available_details,
                }
                for result in results
            ],
        },
    )


@permission_required("cms.view_contact")
def get_contact(
    request: HttpRequest,
    contact_id: int,
    region_slug: str | None = None,
) -> str:
    """
    Retrieves the rendered HTML representation of a contact.

    :param request: The current request
    :param contact_id: The ID of the contact to retrieve
    :param region_slug: The slug of the current region
    :return: HTML representation of the requested contact
    """
    contact = get_object_or_404(Contact, pk=contact_id)

    wanted = request.GET.get("details", "").split(",")
    return render(
        request, "contacts/contact_card.html", {"contact": contact, "wanted": wanted}
    )


@permission_required("cms.view_contact")
def get_contact_raw(
    request: HttpRequest,
    contact_id: int,
    region_slug: str | None = None,
) -> str:
    """
    Retrieves the short representation of a single contact, and returns it
    in the same format as a contact search single completion.

    :param request: The current request
    :param contact_id: The ID of the contact to retrieve
    :param region_slug: The slug of the current region
    :return: Short representation of the requested contact
    """
    contact = get_object_or_404(Contact, pk=contact_id)
    return JsonResponse(
        {
            "data": {
                "url": contact.absolute_url,
                "name": contact.get_repr_short,
                "details": contact.available_details,
            }
        }
    )
