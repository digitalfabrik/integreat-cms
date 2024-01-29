"""
This module contains action methods for the author chat
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from ...forms import ChatMessageForm
from ...models import ChatMessage

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


# pylint: disable=unused-argument
def send_chat_message(
    request: HttpRequest, region_slug: str | None = None
) -> HttpResponse:
    """
    Send chat message

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    """
    chat_form = ChatMessageForm(data=request.POST, sender=request.user)

    if not chat_form.is_valid():
        logger.debug(
            "Invalid ChatMessageForm submitted by %r with errors: %r",
            request.user,
            chat_form.errors,
        )
        # Return HTTP 400 Bad Request if invalid form data was submitted
        return JsonResponse(chat_form.errors, status=400)

    message = chat_form.save()
    logger.debug("%r created", message)

    return render(
        request,
        "chat/_chat_messages.html",
        {
            "chat_messages": request.user.unread_chat_messages,
            "chat_last_visited": request.user.update_chat_last_visited(),
        },
        status=201,  # HTTP 201 Created
    )


@require_POST
# pylint: disable=unused-argument
def delete_chat_message(
    request: HttpRequest, region_slug: str | None = None, message_id: int | None = None
) -> JsonResponse:
    """
    Delete chat message

    :param request: The current request
    :param region_slug: The slug of the current region
    :param message_id: The id of the message
    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to delete the specific message

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    """
    message = get_object_or_404(ChatMessage, id=message_id)

    if not request.user.has_perm("cms.delete_chat_message_object", message):
        # If the user is neither superuser or staff, nor the sender of the message, he cannot delete it
        raise PermissionDenied(
            f"{request.user!r} does not have the permission to delete {message!r}"
        )

    message.delete()
    logger.debug("%r deleted by %r", message, request.user)

    return JsonResponse(
        {
            "success": True,
            "status": "The chat message was successfully deleted.",
            "message": str(message),
        }
    )
