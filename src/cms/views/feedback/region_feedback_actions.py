"""
This module contains action methods for feedack items (archive, restore, ...)
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from ...decorators import region_permission_required, permission_required
from ...models import Feedback, Region

logger = logging.getLogger(__name__)


@require_POST
@login_required
@region_permission_required
@permission_required("cms.change_feedback")
def mark_region_feedback_as_read(request, region_slug):
    """
    Set read flag for a list of feedback items

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: A redirection to the region feedback list
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)

    selected_ids = request.POST.getlist("selected_ids[]")
    Feedback.objects.filter(
        id__in=selected_ids, region=region, is_technical=False
    ).update(read_by=request.user)

    logger.debug(
        "Feedback objects %r marked as read by %r",
        selected_ids,
        request.user,
    )
    messages.success(request, _("Feedback was successfully marked as read"))

    return redirect("region_feedback", region_slug=region_slug)


@require_POST
@login_required
@region_permission_required
@permission_required("cms.change_feedback")
def mark_region_feedback_as_unread(request, region_slug):
    """
    Unset read flag for a list of feedback items

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: A redirection to the region feedback list
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)

    selected_ids = request.POST.getlist("selected_ids[]")
    Feedback.objects.filter(
        id__in=selected_ids, region=region, is_technical=False
    ).update(read_by=None)

    logger.debug(
        "Feedback objects %r marked as unread by %r",
        selected_ids,
        request.user,
    )
    messages.success(request, _("Feedback was successfully marked as unread"))

    return redirect("region_feedback", region_slug=region_slug)


@require_POST
@login_required
@region_permission_required
@permission_required("cms.delete_feedback")
def delete_region_feedback(request, region_slug):
    """
    Delete a list of feedback items

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: A redirection to the region feedback list
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)

    selected_ids = request.POST.getlist("selected_ids[]")
    Feedback.objects.filter(
        id__in=selected_ids, region=region, is_technical=False
    ).delete()

    logger.info("Feedback objects %r deleted by %r", selected_ids, request.user)
    messages.success(request, _("Feedback was successfully deleted"))

    return redirect("region_feedback", region_slug=region_slug)
