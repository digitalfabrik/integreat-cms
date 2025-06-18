"""
This module provides the API endpoints for the public chat API
"""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ....cms.models import ABTester, Language, Region, UserChat
from ...decorators import json_response, rate_limit
from .utils.chat_bot import (
    celery_translate_and_answer_question,
    celery_translate_answer,
    celery_translate_question,
)

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


@csrf_exempt
@json_response
@rate_limit
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


def get_or_create_user_chat(
    request: HttpRequest, device_id: str, language: Language
) -> UserChat | None:
    """
    Get existing UserChat or create a new one if the HTTP method is POST.

    :param request: Django request
    :param device_id: UUID of the app device
    :param language_slug: slug of language that is used by the app
    """
    if user_chat := UserChat.objects.current_chat(device_id):
        return user_chat
    if request.method == "POST":
        return UserChat.objects.create(
            region=request.region,
            device_id=device_id,
            language=language,
        )
    return None


def process_chat_payload(
    request: HttpRequest, device_id: str, language_slug: str
) -> JsonResponse:
    """
    Create or get UserChat object and return list of messages. Save new message
    or updated Zammad ticket attributes.

    :param request: Django request
    :param device_id: UUID of the app device
    :param language_slug: slug of language that is used by the app
    """
    language = Language.objects.get(slug=language_slug)
    if (user_chat := get_or_create_user_chat(request, device_id, language)) is None:
        return JsonResponse({"error": "Chat not found."}, status=404)
    if request.POST.get("message"):
        user_chat.save_message(
            message=request.POST.get("message"), internal=False, automatic_message=False
        )
        user_chat.language = language
        user_chat.save()
    if request.POST.get("evaluation_consent"):
        user_chat.save_evaluation_consent(request.POST.get("evaluation_consent"))
    return JsonResponse(user_chat.as_dict())


@csrf_exempt
@json_response
@rate_limit
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
    try:
        return process_chat_payload(request, device_id, language_slug)
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        ValueError,
    ):
        logger.exception("Could not connect to Zammad")
        return JsonResponse(
            {
                "error": "An error occurred while attempting to connect to the chat server."
            },
            status=500,
        )


def is_app_user_message(webhook_message: dict) -> bool:
    """
    Check if message originates from app user

    param webhook_message: Zammad webhook ticket dict
    """
    return (
        webhook_message["article"]["created_by"]["login"]
        == settings.INTEGREAT_CHAT_CMS_USER_MAIL
        and webhook_message["article"]["sender"] == "Customer"
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
    message_timestamp = datetime.fromisoformat(webhook_message["article"]["created_at"])

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
        celery_translate_question.apply_async(
            args=[message_text, region.slug, webhook_message["ticket"]["id"]]
        )
    elif is_app_user_message(webhook_message):
        actions.append("question translation and answering queued")
        celery_translate_and_answer_question.apply_async(
            args=[message_timestamp, region.slug, webhook_message["ticket"]["id"]],
        )
    else:
        actions.append("answer translation queued")
        celery_translate_answer.apply_async(
            args=[message_text, region.slug, webhook_message["ticket"]["id"]],
        )
    return JsonResponse(
        {
            "original_message": message_text,
            "region": region.slug,
            "actions": actions,
        },
    )
