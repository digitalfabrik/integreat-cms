"""
This module contains action methods for the author chat
"""
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from ...forms import ChatMessageForm
from ...models import ChatMessage

logger = logging.getLogger(__name__)


@login_required
def send_chat_message(request):
    """
    Send chat message

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    chat_form = ChatMessageForm(request.POST, sender=request.user)

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
            "chat_messages": request.user.profile.unread_chat_messages,
            "chat_last_visited": request.user.profile.update_chat_last_visited(),
        },
        status=201,  # HTTP 201 Created
    )


@login_required
def delete_chat_message(request, message_id):
    """
    Delete chat message

    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to delete the specific message

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    message = get_object_or_404(ChatMessage, id=message_id)

    if not request.user.has_perm("cms.delete_chat_message", message):
        # If the user is neither superuser or staff, nor the sender of the message, he cannot delete it
        logger.warning(
            "PermissionDenied: %r tried to delete %r",
            request.user.profile,
            message,
        )
        raise PermissionDenied

    message.delete()
    logger.debug("%r deleted by %r", message, request.user.profile)

    return JsonResponse(
        {
            "success": True,
            "status": "The chat message was successfully deleted.",
            "message": str(message),
        }
    )
