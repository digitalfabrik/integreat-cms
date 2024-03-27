"""
This module contains action methods for feedback items (archive, restore, ...)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import magic
from cacheops import invalidate_model, invalidate_obj
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from tablib import Dataset
from tablib.formats import registry as format_registry

from ...decorators import permission_required
from ...models import Feedback
from .feedback_resource import FeedbackResource

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_feedback")
def mark_region_feedback_as_read(
    request: HttpRequest, region_slug: str
) -> HttpResponseRedirect:
    """
    Set read flag for a list of feedback items

    :param request: Object representing the user call
    :param region_slug: The slug of the current region
    :return: A redirection to the region feedback list
    """

    region = request.region

    selected_ids = request.POST.getlist("selected_ids[]")
    selected_feedback = Feedback.objects.filter(
        id__in=selected_ids, region=region, is_technical=False
    )
    for feedback in selected_feedback:
        invalidate_obj(feedback)
        if hasattr(feedback, "feedback_ptr"):
            invalidate_obj(feedback.feedback_ptr)
    selected_feedback.update(read_by=request.user)

    logger.debug(
        "Feedback objects %r marked as read by %r",
        selected_ids,
        request.user,
    )
    messages.success(request, _("Feedback was successfully marked as read"))

    return redirect("region_feedback", region_slug=region_slug)


@require_POST
@permission_required("cms.change_feedback")
def mark_region_feedback_as_unread(
    request: HttpRequest, region_slug: str
) -> HttpResponseRedirect:
    """
    Unset read flag for a list of feedback items

    :param request: Object representing the user call
    :param region_slug: The slug of the current region
    :return: A redirection to the region feedback list
    """

    region = request.region

    selected_ids = request.POST.getlist("selected_ids[]")
    selected_feedback = Feedback.objects.filter(
        id__in=selected_ids, region=region, is_technical=False
    )
    for feedback in selected_feedback:
        invalidate_obj(feedback)
        if hasattr(feedback, "feedback_ptr"):
            invalidate_obj(feedback.feedback_ptr)
    selected_feedback.update(read_by=None)

    logger.debug(
        "Feedback objects %r marked as unread by %r",
        selected_ids,
        request.user,
    )
    messages.success(request, _("Feedback was successfully marked as unread"))

    return redirect("region_feedback", region_slug=region_slug)


@require_POST
@permission_required("cms.change_feedback")
def archive_region_feedback(
    request: HttpRequest, region_slug: str
) -> HttpResponseRedirect:
    """
    Archive a list of feedback items

    :param request: Object representing the user call
    :param region_slug: The slug of the current region
    :return: A redirection to the region feedback list
    """

    region = request.region

    selected_ids = request.POST.getlist("selected_ids[]")
    Feedback.objects.filter(
        id__in=selected_ids, region=region, is_technical=False
    ).update(archived=True)
    invalidate_model(Feedback)

    logger.info("Feedback objects %r archived by %r", selected_ids, request.user)
    messages.success(request, _("Feedback was successfully archived"))

    return redirect("region_feedback", region_slug=region_slug)


@require_POST
@permission_required("cms.change_feedback")
def restore_region_feedback(
    request: HttpRequest, region_slug: str
) -> HttpResponseRedirect:
    """
    Restore a list of feedback items

    :param request: Object representing the user call
    :param region_slug: The slug of the current region
    :return: A redirection to the region feedback list
    """

    region = request.region

    selected_ids = request.POST.getlist("selected_ids[]")
    Feedback.objects.filter(
        id__in=selected_ids, region=region, is_technical=False
    ).update(archived=False)
    invalidate_model(Feedback)

    logger.info("Feedback objects %r restored by %r", selected_ids, request.user)
    messages.success(request, _("Feedback was successfully restored"))

    return redirect("region_feedback_archived", region_slug=region_slug)


@require_POST
@permission_required("cms.delete_feedback")
def delete_region_feedback(
    request: HttpRequest, region_slug: str
) -> HttpResponseRedirect:
    """
    Delete a list of feedback items

    :param request: Object representing the user call
    :param region_slug: The slug of the current region
    :return: A redirection to the region feedback list
    """

    region = request.region

    selected_ids = request.POST.getlist("selected_ids[]")
    Feedback.objects.filter(
        id__in=selected_ids, region=region, is_technical=False
    ).delete()

    logger.info("Feedback objects %r deleted by %r", selected_ids, request.user)
    messages.success(request, _("Feedback was successfully deleted"))

    return redirect("region_feedback", region_slug=region_slug)


# pylint: disable=unused-argument
@require_POST
@permission_required("cms.view_feedback")
def export_region_feedback(
    request: HttpRequest,
    region_slug: str,
    file_format: str,
) -> HttpResponse:
    """
    Export a list of feedback items

    :param request: Object representing the user call
    :param region_slug: The slug of the current region
    :param file_format: The export format
    :return: Response with file
    """
    selected_ids = request.POST.getlist("selected_ids[]")
    selected_feedback = Feedback.objects.filter(
        id__in=selected_ids, region=request.region, is_technical=False
    )

    resource = FeedbackResource()
    dataset = Dataset(
        *(resource.export_resource(obj) for obj in selected_feedback),
        headers=resource.export().headers,
    )

    if file_format in (f.title for f in format_registry.formats()):
        blob = getattr(dataset, file_format)
        mime = magic.from_buffer(blob, mime=True)
        response = HttpResponse(blob, content_type=mime)
    else:
        raise ValueError(f"Unknown export format {file_format}")
    response["Content-Disposition"] = (
        f'attachment; filename="Integreat_{request.region}_feedback.{file_format}'
    )
    return response
