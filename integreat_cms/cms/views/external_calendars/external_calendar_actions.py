import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ...decorators import permission_required

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.delete_externalcalendar")
def delete_external_calendar(
    request: HttpRequest,
    calendar_id: int,
    region_slug: str,
) -> HttpResponseRedirect:
    """
    Delete external calendar

    :param request: The current request
    :param calendar_id: The id of the calendar that should be deleted
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.events.external_calendars.ExternalCalendarList`
    """
    region = request.region
    calendar = get_object_or_404(region.external_calendars, id=calendar_id)

    logger.info("%r deleted by %r", calendar, request.user)

    calendar.delete()
    messages.success(request, _("External calendar was successfully deleted"))

    return redirect(
        "external_calendar_list",
        **{
            "region_slug": region_slug,
        },
    )
