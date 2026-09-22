"""
This module contains action methods for events (archive, restore, ...)
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ...constants import status
from ...decorators import permission_required
from ...models import PlaceTranslation, Region
from ...models.events.event import CouldNotBeCopied
from ...utils.event_utils import get_filtered_events_url

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_event")
def archive(
    request: HttpRequest,
    event_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Set archived flag for an event

    :param request: Object representing the user call
    :param event_id: internal id of the event to be archived
    :param region_slug: slug of the region which the event belongs to
    :param language_slug: current GUI language slug
    :return: The rendered template response
    """
    region = request.region
    event = get_object_or_404(region.events, id=event_id)

    event.archive()

    logger.debug("%r archived by %r", event, request.user)
    messages.success(request, _("Event was successfully archived"))

    return redirect(
        "events",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.change_event")
def copy(
    request: HttpRequest,
    event_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Duplicates the given event and all of its translations.

    :param request: Object representing the user call
    :param event_id: internal id of the event to be copied
    :param region_slug: slug of the region which the event belongs to
    :param language_slug: current GUI language slug
    :return: The rendered template response
    """
    region = request.region
    event = get_object_or_404(region.events, id=event_id)

    try:
        event.copy(request.user)
    except CouldNotBeCopied:
        messages.error(
            request,
            _("Event couldn't be copied because it's from an external calendar"),
        )
        return redirect(get_filtered_events_url(request, region_slug, language_slug))

    logger.debug("%r copied by %r", event, request.user)
    messages.success(request, _("Event was successfully copied"))

    return redirect(get_filtered_events_url(request, region_slug, language_slug))


@require_POST
@permission_required("cms.change_event")
def restore(
    request: HttpRequest,
    event_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Remove archived flag for an event

    :param request: Object representing the user call
    :param event_id: internal id of the event to be un-archived
    :param region_slug: slug of the region which the event belongs to
    :param language_slug: current GUI language slug
    :return: The rendered template response
    """
    region = request.region
    event = get_object_or_404(region.events, id=event_id)

    event.restore()

    logger.debug("%r restored by %r", event, request.user)
    messages.success(request, _("Event was successfully restored"))

    return redirect(
        "events",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.delete_event")
def delete(
    request: HttpRequest,
    event_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Delete a single event

    :param request: Object representing the user call
    :param event_id: internal id of the event to be deleted
    :param region_slug: slug of the region which the event belongs to
    :param language_slug: current GUI language slug
    :return: The rendered template response
    """
    region = request.region
    event = get_object_or_404(region.events, id=event_id)

    logger.info("%r deleted by %r", event, request.user)

    event.delete()
    messages.success(request, _("Event was successfully deleted"))

    return redirect(get_filtered_events_url(request, region_slug, language_slug))


@require_POST
@permission_required("cms.view_event")
def search_place_ajax(
    request: HttpRequest,
    region_slug: str,
) -> HttpResponse:
    """
    AJAX endpoint for searching places

    :param request: Object representing the user call
    :return: The rendered template response
    """
    data = json.loads(request.body.decode("utf-8"))

    place_query = data.get("query_string")
    create_place_option = data.get("create_place_option")

    logger.debug('Ajax call: Live search for places with query "%r"', place_query)

    region = get_object_or_404(Region, slug=data.get("region_slug"))

    # All latest versions of a place (one for each language)
    latest_public_place_versions = (
        PlaceTranslation.objects.filter(place=OuterRef("pk"), status=status.PUBLIC)
        .order_by("language__pk", "-version")
        .distinct("language")
        .values("id")
    )
    # All places which are not archived and have a latest public revision which contains the query
    place_query_result = (
        region.places.prefetch_related("translations")
        .filter(
            archived=False,
            translations__in=Subquery(latest_public_place_versions),
            translations__title__icontains=place_query,
        )
        .distinct()
    )

    return render(
        request,
        "_place_query_result.html",
        {
            "place_query": place_query,
            "place_query_result": place_query_result,
            "create_place_option": create_place_option,
            "region": region,
        },
    )
