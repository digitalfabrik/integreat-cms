"""
This module provides the API endpoints for the public chat API
"""

from __future__ import annotations

import json
import logging
import random
from io import BytesIO
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from ....cms.models import ABTester, Language, Region, UserChat
from ...decorators import json_response, rate_limit
from .utils.chat_bot import (
    celery_translate_and_answer_question,
    celery_translate_answer,
    celery_translate_question,
)

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile
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

    If a chat exists but has been inactive long enough that its Zammad ticket is
    assumed to be gone (Zammad's ticket retention is shorter than ours), a new chat
    is started for the same device id on POST requests.

    :param request: Django request
    :param device_id: UUID of the app device
    :param language_slug: slug of language that is used by the app
    """
    if (user_chat := UserChat.objects.current_chat(device_id)) and (
        not user_chat.is_expired
    ):
        return user_chat
    if request.method == "POST":
        return UserChat.objects.create(
            region=request.region,
            device_id=device_id,
            language=language,
        )
    return None


def validate_attachments(attachments: list[UploadedFile]) -> str | None:
    """
    Validate a list of uploaded chat attachments against the configured
    size, MIME type and count restrictions.

    :param attachments: uploaded files to validate
    :return: an error message if validation fails, otherwise ``None``
    """
    for attachment in attachments:
        if (
            attachment.size is None
            or attachment.size > settings.INTEGREAT_CHAT_ATTACHMENT_MAX_SIZE
        ):
            return f"Attachment '{attachment.name}' exceeds the maximum allowed size."
        if (
            attachment.content_type
            not in settings.INTEGREAT_CHAT_ATTACHMENT_ALLOWED_MIME_TYPES
        ):
            return f"Attachment '{attachment.name}' has an unsupported file type."
    if len(attachments) > settings.INTEGREAT_CHAT_ATTACHMENT_MAX_COUNT:
        return f"At most {settings.INTEGREAT_CHAT_ATTACHMENT_MAX_COUNT} attachments can be sent per message."
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
    attachments = request.FILES.getlist("attachment")
    if attachments and (error := validate_attachments(attachments)) is not None:
        return JsonResponse({"error": error}, status=400)
    message_text = request.POST.get("message", "")
    if message_text or attachments:
        response = user_chat.save_message(
            message=message_text,
            internal=False,
            automatic_message=False,
            attachments=attachments or None,
        )
        user_chat.language = language
        user_chat.save()
        if message_text and response is not None:
            if user_chat.automatic_answers:
                user_chat.processing_answer = True  # type: ignore[assignment]
                celery_translate_and_answer_question.apply_async(
                    args=[
                        parse_datetime(response["updated_at"]),
                        request.region.slug,
                        response["ticket_id"],
                    ],
                )
            else:
                celery_translate_question.apply_async(
                    args=[
                        message_text,
                        request.region.slug,
                        response["ticket_id"],
                    ]
                )
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


@csrf_exempt
@json_response
@rate_limit
def chat_attachment(
    request: HttpRequest,
    region_slug: str,
    device_id: str,
    article_id: int,
    attachment_id: int,
) -> FileResponse | JsonResponse:
    """
    Download an attachment from the current chat ticket of the given device.

    The attachment must belong to a non-internal article of the device's current
    Zammad ticket; otherwise a 404 is returned.

    :param request: Django request
    :param region_slug: slug of the region
    :param device_id: ID of the device requesting the attachment
    :param article_id: ID of the Zammad article the attachment belongs to
    :param attachment_id: ID of the attachment within the article
    :return: file response or JSON error
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
    user_chat = UserChat.objects.current_chat(device_id, region=request.region)
    if user_chat is None or user_chat.is_expired:
        return JsonResponse({"error": "Chat not found."}, status=404)
    try:
        result = user_chat.get_attachment(article_id, attachment_id)
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
    if result is None:
        return JsonResponse({"error": "Attachment not found."}, status=404)
    content, content_type, filename = result
    return FileResponse(
        BytesIO(content),
        content_type=content_type,
        as_attachment=True,
        filename=filename,
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
    Receive webhooks from Zammad to update the latest article translation.

    Optional feature: if a Zammad has an object attribute "device_id" for tickets,
    we can use this to directly fetch the corresponding chat from our database.
    This allows multiple regions to use the same Zammad server. As not all Zammad
    servers have this configured, we still need to support the old method were we
    fetch the UserChat object identified by the region token and Zammad ticket id.
    """
    token_region = get_object_or_404(
        Region,
        zammad_webhook_token=request.GET.get("token", None),
    )
    webhook_message = json.loads(request.body)

    if (
        "device_id" in webhook_message["ticket"]
        and webhook_message["ticket"]["device_id"]
    ):
        zammad_chat = get_object_or_404(
            UserChat, device_id=webhook_message["ticket"]["device_id"]
        )
    else:  # legacy support
        zammad_chat = get_object_or_404(
            UserChat, zammad_id=webhook_message["ticket"]["id"], region=token_region
        )

    region = zammad_chat.region

    if not region.integreat_chat_enabled:
        return JsonResponse({"status": "Integreat Chat disabled"})

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
        actions.append("question translation already tasked")
    elif is_app_user_message(webhook_message):
        actions.append("question translation and answering already tasked")
    else:
        actions.append("human answer translation queued")
        cache.delete(f"{zammad_chat.region.slug}_{zammad_chat.device_id}")
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
