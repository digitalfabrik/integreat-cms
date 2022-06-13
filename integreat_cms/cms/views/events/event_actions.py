"""
This module contains action methods for events (archive, restore, ...)
"""
import json
import logging

from django.contrib import messages
from django.db.models import Subquery, OuterRef
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from linkcheck.models import Link

from ...constants import status
from ...decorators import permission_required
from ...models import Region, POITranslation

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_event")
def archive(request, event_id, region_slug, language_slug):
    """
    Set archived flag for an event

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param event_id: internal id of the event to be archived
    :type event_id: int

    :param region_slug: slug of the region which the event belongs to
    :type region_slug: str

    :param language_slug: current GUI language slug
    :type language_slug: str

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    region = request.region
    event = get_object_or_404(region.events, id=event_id)

    event.archived = True
    event.save()

    # Delete related link objects as they are no longer required
    Link.objects.filter(event_translation__event=event).delete()

    logger.debug("%r archived by %r", event, request.user)
    messages.success(request, _("Event was successfully archived"))

    return redirect(
        "events",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        }
    )


@require_POST
@permission_required("cms.change_event")
def copy(request, event_id, region_slug, language_slug):
    """
    Duplicates the given event and all of its translations.

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param event_id: internal id of the event to be copied
    :type event_id: int

    :param region_slug: slug of the region which the event belongs to
    :type region_slug: str

    :param language_slug: current GUI language slug
    :type language_slug: str

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
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
def restore(request, event_id, region_slug, language_slug):
    """
    Remove archived flag for an event

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param event_id: internal id of the event to be un-archived
    :type event_id: int

    :param region_slug: slug of the region which the event belongs to
    :type region_slug: str

    :param language_slug: current GUI language slug
    :type language_slug: str

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    region = request.region
    event = get_object_or_404(region.events, id=event_id)

    event.archived = False
    event.save()

    # Restore related link objects
    for translation in event.translations.distinct("event__pk", "language__pk"):
        # The post_save signal will create link objects from the content
        translation.save(update_timestamp=False)

    logger.debug("%r restored by %r", event, request.user)
    messages.success(request, _("Event was successfully restored"))

    return redirect(
        "events",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        }
    )


@require_POST
@permission_required("cms.delete_event")
def delete(request, event_id, region_slug, language_slug):
    """
    Delete a single event

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param event_id: internal id of the event to be deleted
    :type event_id: int

    :param region_slug: slug of the region which the event belongs to
    :type region_slug: str

    :param language_slug: current GUI language slug
    :type language_slug: str

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
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
        }
    )


@require_POST
@permission_required("cms.view_event")
# pylint: disable=unused-argument
def search_poi_ajax(request, region_slug):
    """
    AJAX endpoint for searching POIs

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param region_slug: The current regions slug
    :type region_slug: str

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    data = json.loads(request.body.decode("utf-8"))

    poi_query = data.get("query_string")
    create_poi_option = data.get("create_poi_option")

    logger.debug('Ajax call: Live search for POIs with query "%r"', poi_query)

    region = get_object_or_404(Region, slug=data.get("region_slug"))

    # All latest revisions of a POI (one for each language)
    latest_public_poi_revisions = (
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
            translations__in=Subquery(latest_public_poi_revisions),
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
