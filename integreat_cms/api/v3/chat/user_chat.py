"""
This module provides the API endpoints for the Integreat Chat API
"""

from __future__ import annotations

import json
import logging
import random
from typing import TYPE_CHECKING

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ....cms.models import ABTester, Language, Region, UserChat
from ...decorators import json_response
from .utils.chat_bot import (
    process_translate_answer,
    process_translate_question,
    process_user_message,
)

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


@csrf_exempt
@json_response
def is_chat_enabled_for_user(
    request: HttpRequest,
    region_slug: str,
    device_id: str,
) -> JsonResponse:
    """
    Function to check if the chat feature is enabled for the given region and the given user.

    :param request: Django request
    :param device_id: ID of the user attempting to use the chat
    :return: JSON object according to APIv3 chat endpoint definition
    """
    if existing_user := ABTester.objects.filter(device_id=device_id).first():
        return JsonResponse({"is_chat_enabled": existing_user.is_tester}, status=200)

    is_enabled = bool(
        request.region.zammad_url
        and request.region.zammad_access_token
        and random.random() < (0.01 * request.region.chat_beta_tester_percentage),  # noqa: S311
    )
    ABTester.objects.create(
        device_id=device_id,
        region=request.region,
        is_tester=is_enabled,
    )
    return JsonResponse({"is_chat_enabled": is_enabled}, status=200)


@csrf_exempt
@json_response
def chat(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    device_id: str,
) -> JsonResponse | HttpResponse:
    """
    Function to send a new message in the current chat of a specified device_id,
    or to create one if no chat exists or the user requested a new one.

    :param request: Django request
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

    if user_chat := UserChat.objects.current_chat(device_id):
        # checking the current chat for ratelimiting purposes is sufficient,
        # since new chat creation also depends on passing this check
        if user_chat.ratelimit_exceeded():
            logger.warning(
                "Client with device ID %s has exceeded their ratelimit.",
                device_id,
            )
            return JsonResponse({"error": "You're doing that too often."}, status=429)
        user_chat.record_hit()
    else:
        return JsonResponse({"error": "Chat not found."}, status=404)
    if request.POST.get("message"):
        user_chat.save_message(request.POST.get("message"), False, False)
    if request.POST.get("evaluation_consent"):
        user_chat.save_evaluation_consent(request.POST.get("evaluation_consent"))
    return JsonResponse(user_chat.as_dict())


def is_app_user_message(webhook_message: dict) -> bool:
    """
    Check if message originates from app user

    param webhook_message: Zammad webhook ticket dict
    """
    return (
        webhook_message["article"]["created_by"]["login"]
        == "tech+integreat-cms@tuerantuer.org"
    )


@csrf_exempt
@json_response
def zammad_webhook(request: HttpRequest) -> JsonResponse:
    """
    Receive webhooks from Zammad to update the latest article translation
    """
    region = get_object_or_404(
        Region,
        zammad_webhook_token=request.GET.get("token", None),
    )
    if not region.integreat_chat_enabled:
        return JsonResponse({"status": "Integreat Chat disabled"})
    webhook_message = json.loads(request.body)
    message_text = webhook_message["article"]["body"]

    actions = []
    if webhook_message["article"]["internal"]:
        return JsonResponse(
            {
                "region": region.slug,
                "results": "skipped internal message",
            },
        )
    if (
        is_app_user_message(webhook_message)
        and not webhook_message["ticket"]["automatic_answers"]
    ):
        actions.append("question translation queued")
        process_translate_question.apply_async(
            args=[message_text, region.slug, webhook_message["ticket"]["id"]]
        )
    elif is_app_user_message(webhook_message):
        actions.append("question translation and answering queued")
        process_user_message.apply_async(
            args=[region.slug, webhook_message["ticket"]["id"]],
        )
    else:
        actions.append("answer translation queued")
        process_translate_answer.apply_async(
            args=[message_text, region.slug, webhook_message["ticket"]["id"]],
        )
    return JsonResponse(
        {
            "original_message": message_text,
            "region": region.slug,
            "actions": actions,
        },
    )
