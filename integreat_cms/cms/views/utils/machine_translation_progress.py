"""
This module contains the API call handler for polling the progress of an
asynchronous machine translation Celery task.
"""

from __future__ import annotations

from typing import Literal, TYPE_CHECKING

from celery import states
from celery.result import AsyncResult
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.translation import gettext as _

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest


def _get_failure_reason(raw_message: str) -> str:
    """
    Translate a known, internal validation-failure message into user-facing
    text.

    :param raw_message: The exception's own message, as raised
    :return: The translated reason to show the user, or the original message
        if it isn't one of the known cases
    """
    if raw_message == "User not found":
        return _("the triggering user could not be found")
    if raw_message == "Region not found":
        return _("the requested region could not be found")
    if raw_message == "Content type not found":
        return _("the requested content type is not supported")
    return raw_message


def _get_result_details(result: AsyncResult) -> Any:
    """
    ``AsyncResult.info`` returns a reconstructed exception *instance* for a
    failed task, not the plain dict our own successful/pending states use -
    and that isn't JSON-serializable directly. Convert it to the same
    ``{"message": ...}`` shape already used elsewhere in this module instead,
    with the full translated banner text so the frontend can display it
    verbatim, without composing any text of its own.

    :param result: The Celery result to read
    :return: JSON-safe details for the current state
    """
    if result.state == states.FAILURE:
        return {
            "message": _(
                "Machine translation of multiple pages was not successful. "
                "The process was aborted because {reason}. Please try again."
            ).format(reason=_get_failure_reason(str(result.info)))
        }
    return result.info


def get_machine_translation_task_progress(
    request: HttpRequest,
    region_slug: str,
    model_type: Literal["page", "event", "poi", "pushnotification"],
    task_id: str,
) -> JsonResponse:
    """
    Report the current progress of an asynchronous machine translation Celery
    task, identified directly by its task id. Used by callers (e.g. the
    content list views) that already know which task governs a whole batch
    of objects, because the task id was resolved once at render time and
    grouped client-side. Every object in that batch shares the same task, so
    checking the task once is equivalent to - and cheaper than - checking
    each object.

    :param request: The current request
    :param region_slug: The slug of the current region
    :param model_type: The content type being translated (e.g. "page")
    :param task_id: The id of the Celery task to check
    :return: A JSON object describing the current translation progress
    """
    if not request.user.has_perm(f"cms.view_{model_type}"):
        raise PermissionDenied

    result = AsyncResult(task_id)
    if result.state != states.PENDING and (
        result.kwargs.get("region_id") != request.region.id
        or model_type != result.kwargs.get("content_type")
    ):
        raise PermissionDenied

    return JsonResponse(
        {"status": result.state, "details": _get_result_details(result)}
    )
