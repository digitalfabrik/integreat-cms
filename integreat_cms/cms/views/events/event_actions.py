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
from ...models import POITranslation, Region

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_event")
def archive(
    request: HttpRequest, event_id: int, region_slug: str, language_slug: str
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
    request: HttpRequest, event_id: int, region_slug: str, language_slug: str
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

    event.copy(request.user)

    logger.debug("%r copied by %r", event, request.user)
    messages.success(request, _("Event was successfully copied"))

    return redirect(
        "events", **{"region_slug": region_slug, "language_slug": language_slug}
    )


@require_POST
@permission_required("cms.change_event")
def restore(
    request: HttpRequest, event_id: int, region_slug: str, language_slug: str
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
    request: HttpRequest, event_id: int, region_slug: str, language_slug: str
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

    if event.recurrence_rule:
        event.recurrence_rule.delete()
    event.delete()
    messages.success(request, _("Event was successfully deleted"))

    return redirect(
        "events",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.view_event")
# pylint: disable=unused-argument
def search_poi_ajax(request: HttpRequest, region_slug: str) -> HttpResponse:
    """
    AJAX endpoint for searching POIs

    :param request: Object representing the user call
    :param region_slug: The current regions slug
    :return: The rendered template response
    """
    data = json.loads(request.body.decode("utf-8"))

    poi_query = data.get("query_string")
    create_poi_option = data.get("create_poi_option")

    logger.debug('Ajax call: Live search for POIs with query "%r"', poi_query)

    region = get_object_or_404(Region, slug=data.get("region_slug"))

    # All latest versions of a POI (one for each language)
    latest_public_poi_versions = (
        POITranslation.objects.filter(poi=OuterRef("pk"), status=status.PUBLIC)
        .order_by("language__pk", "-version")
        .distinct("language")
        .values("id")
    )
    # All POIs which are not archived and have a latest public revision which contains the query
    poi_query_result = (
        region.pois.prefetch_related("translations")
        .filter(
            archived=False,
            translations__in=Subquery(latest_public_poi_versions),
            translations__title__icontains=poi_query,
        )
        .distinct()
    )

    return render(
        request,
        "events/_poi_query_result.html",
        {
            "poi_query": poi_query,
            "poi_query_result": poi_query_result,
            "create_poi_option": create_poi_option,
            "region": region,
        },
    )
