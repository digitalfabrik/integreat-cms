"""
This module provides the API endpoints for the Integreat Chat API
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from ....cms.models import ABTester, AttachmentMap, UserChat
from ...decorators import json_response
from .zammad_api import ZammadChatAPI

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


def response_or_error(result: dict) -> JsonResponse:
    """
    Helper function to extract the status code from the API response

    :param result: an API call's result
    :return: json response with appropriate status code
    """
    if result.get("status"):
        return JsonResponse(result, status=result.pop("status"))
    return JsonResponse(result)


def get_attachment(
    client: ZammadChatAPI,
    user_chat: UserChat | None,
    attachment_id: str,
) -> JsonResponse | HttpResponse:
    """
    Function to retrieve an attachment given the correct attachment_id

    :param client: the Zammad API client to use
    :param user_chat: the device_id's current chat (if one exists)
    :param attachment_id: ID of the requested attachment
    :return: JSON object according to APIv3 offers endpoint definition
    """
    if (
        not (
            attachment_map := AttachmentMap.objects.filter(
                random_hash=attachment_id
            ).first()
        )
        or (not user_chat)
        or attachment_map.user_chat != user_chat
    ):
        logger.warning(
            "An attachment with ID %s was requested, but does not exist for user chat %r.",
            attachment_id,
            user_chat,
        )
        return JsonResponse(
            {"error": "The requested attachment does not exist."},
            status=404,
        )
    response = client.get_attachment(attachment_map)
    if isinstance(response, dict):
        return response_or_error(response)
    return HttpResponse(response, content_type=attachment_map.mime_type)


def get_messages(
    request: HttpRequest,
    client: ZammadChatAPI,
    user_chat: UserChat | None,
    device_id: str,
) -> JsonResponse:
    """
    Function to retrieve all messages of the most recent chat for a given device_id

    :param request: Django request
    :param client: the Zammad API client to use
    :param user_chat: the device_id's current chat
    :param device_id: ID of the user requesting the messages
    :return: JSON object according to APIv3 offers endpoint definition
    """
    if not user_chat:
        logger.warning(
            "A chat for device ID %s was requested, but does not exist in %r.",
            device_id,
            request.region,
        )
        return JsonResponse(
            {"error": "The requested chat does not exist. Did you delete it?"},
            status=404,
        )
    return response_or_error(client.get_messages(user_chat))


def send_message(
    request: HttpRequest,
    language_slug: str,
    client: ZammadChatAPI,
    user_chat: UserChat | None,
    device_id: str,
) -> JsonResponse:
    """
    Function to send a new message in the current chat of a specified device_id,
    or to create one if no chat exists or the user requested a new one.

    :param request: Django request
    :param language_slug: language slug
    :param client: the Zammad API client to use
    :param user_chat: the device_id's current chat (if one exists)
    :param device_id: ID of the user requesting the messages
    :return: JSON object according to APIv3 offers endpoint definition
    """
    if request.POST.get("force_new") or not user_chat:
        try:
            chat_id = client.create_ticket(device_id, language_slug)["id"]
            user_chat = UserChat.objects.create(device_id=device_id, zammad_id=chat_id)
        except KeyError:
            logger.warning(
                "Failed to create a new chat in %r",
                request.region,
            )
            return JsonResponse(
                {"error": "An error occurred while attempting to create a new chat."},
                status=500,
            )
    return response_or_error(
        client.send_message(user_chat.zammad_id, request.POST.get("message"))  # type: ignore[union-attr]
    )


@csrf_exempt
@json_response
# pylint: disable=unused-argument
def is_chat_enabled_for_user(
    request: HttpRequest, region_slug: str, device_id: str
) -> JsonResponse:
    """
    Function to check if the chat feature is enabled for the given region and the given user.

    :param request: Django request
    :param region_slug: slug of a region
    :param device_id: ID of the user attempting to use the chat
    :return: JSON object according to APIv3 chat endpoint definition
    """
    if existing_user := ABTester.objects.filter(device_id=device_id).first():
        return JsonResponse({"is_chat_enabled": existing_user.is_tester}, status=200)

    is_enabled = bool(
        request.region.zammad_url
        and request.region.zammad_access_token
        and random.random() < (0.01 * request.region.chat_beta_tester_percentage)
    )
    ABTester.objects.create(
        device_id=device_id, region=request.region, is_tester=is_enabled
    )
    return JsonResponse({"is_chat_enabled": is_enabled}, status=200)


@csrf_exempt
@json_response
# pylint: disable=unused-argument
def chat(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    device_id: str,
    attachment_id: str = "",
) -> JsonResponse | HttpResponse:
    """
    Function to send a new message in the current chat of a specified device_id,
    or to create one if no chat exists or the user requested a new one.

    :param request: Django request
    :param region_slug: slug of a region
    :param language_slug: language slug
    :param device_id: ID of the user requesting the messages
    :param attachment_id: ID of the requested attachment (optional)
    :return: JSON object according to APIv3 chat endpoint definition
    """
    if (
        not request.region.integreat_chat_enabled
        or not request.region.zammad_url
        or not request.region.zammad_access_token
    ):
        return JsonResponse(
            {"error": "No chat server is configured for your region."},
            status=503,
        )

    client = ZammadChatAPI(request.region)
    if user_chat := UserChat.objects.current_chat(device_id):
        # checking the current chat for ratelimiting purposes is sufficient,
        # since new chat creation also depends on passing this check
        if user_chat.ratelimit_exceeded():
            logger.warning(
                "Client with device ID %s has exceeded their ratelimit.", device_id
            )
            return JsonResponse({"error": "You're doing that too often."}, status=429)
        user_chat.record_hit()

    if request.method == "GET" and attachment_id:
        return get_attachment(client, user_chat, attachment_id)
    if request.method == "GET":
        return get_messages(request, client, user_chat, device_id)
    return send_message(request, language_slug, client, user_chat, device_id)
