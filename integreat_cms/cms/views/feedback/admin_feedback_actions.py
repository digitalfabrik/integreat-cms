"""
This module contains action methods for feedback items (archive, restore, ...)
"""
import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from cacheops import invalidate_obj

from ...decorators import permission_required
from ...models import Feedback

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_feedback")
def mark_admin_feedback_as_read(request):
    """
    Set read flag for a list of feedback items

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :return: A redirection to the admin feedback list
    :rtype: ~django.http.HttpResponseRedirect
    """

    selected_ids = request.POST.getlist("selected_ids[]")
    selected_feedback = Feedback.objects.filter(id__in=selected_ids, is_technical=True)
    for feedback in selected_feedback:
        invalidate_obj(feedback)
        if hasattr(feedback, "feedback_ptr"):
            invalidate_obj(feedback.feedback_ptr)
    selected_feedback.update(read_by=request.user)

    logger.debug("Feedback objects %r marked as read by %r", selected_ids, request.user)
    messages.success(request, _("Feedback was successfully marked as read"))

    return redirect("admin_feedback")


@require_POST
@permission_required("cms.change_feedback")
def mark_admin_feedback_as_unread(request):
    """
    Unset read flag for a list of feedback items

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :return: A redirection to the admin feedback list
    :rtype: ~django.http.HttpResponseRedirect
    """

    selected_ids = request.POST.getlist("selected_ids[]")
    selected_feedback = Feedback.objects.filter(id__in=selected_ids, is_technical=True)
    for feedback in selected_feedback:
        invalidate_obj(feedback)
        if hasattr(feedback, "feedback_ptr"):
            invalidate_obj(feedback.feedback_ptr)
    selected_feedback.update(read_by=None)

    logger.debug(
        "Feedback objects %r marked as unread by %r", selected_ids, request.user
    )
    messages.success(request, _("Feedback was successfully marked as unread"))

    return redirect("admin_feedback")


@require_POST
@permission_required("cms.delete_feedback")
def delete_admin_feedback(request):
    """
    Delete a list of feedback items

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :return: A redirection to the admin feedback list
    :rtype: ~django.http.HttpResponseRedirect
    """

    selected_ids = request.POST.getlist("selected_ids[]")
    Feedback.objects.filter(id__in=selected_ids, is_technical=True).delete()

    logger.info("Feedback objects %r deleted by %r", selected_ids, request.user)
    messages.success(request, _("Feedback was successfully deleted"))

    return redirect("admin_feedback")
