"""
Wrapper for the Chat Bot / LLM API
"""

from __future__ import annotations

import requests
from celery import shared_task
from django.conf import settings

from integreat_cms.cms.models import Region, UserChat
from integreat_cms.cms.utils.content_translation_utils import (
    get_public_translation_for_link,
)

from .zammad_api import ZammadChatAPI


def format_message(response: dict) -> str:
    """
    Transform JSON into readable message
    """
    if "answer" not in response or not response["answer"]:
        raise ValueError("Could not format message, no answer attribute in response")
    if "sources" not in response or not response["sources"]:
        return response["answer"]
    sources = "".join(
        [
            f"<li><a href='{settings.WEBAPP_URL}{path}'>{title}</a></li>"
            for path in response["sources"]
            if (title := get_public_translation_for_link(settings.WEBAPP_URL + path))
        ]
    )
    return f"{response['answer']}\n<ul>{sources}</ul>"


def automatic_answer(message: str, region: Region, language_slug: str) -> str | None:
    """
    Get automatic answer to question
    """
    url = (
        f"https://{settings.INTEGREAT_CHAT_BACK_END_DOMAIN}/chatanswers/extract_answer/"
    )
    body = {"message": message, "language": language_slug, "region": region.slug}
    r = requests.post(url, json=body, timeout=120)
    return format_message(r.json())


def automatic_translation(
    message: str, source_language_slug: str, target_language_slug: str
) -> str:
    """
    Use LLM to translate message
    """
    url = f"https://{settings.INTEGREAT_CHAT_BACK_END_DOMAIN}/chatanswers/translate_message/"
    body = {
        "message": message,
        "source_language": source_language_slug,
        "target_language": target_language_slug,
    }
    response = requests.post(url, json=body, timeout=120).json()
    if "status" in response and response["status"] == "success":
        return response["translation"]
    raise ValueError("Did not receive success response for translation request.")


@shared_task
def process_user_message(
    message_text: str, region_slug: str, zammad_ticket_id: int
) -> None:
    """
    Process the message from an Integreat App user
    """
    zammad_chat = UserChat.objects.get(zammad_id=zammad_ticket_id)
    region = Region.objects.get(slug=region_slug)
    client = ZammadChatAPI(region)
    if translation := automatic_translation(
        message_text, zammad_chat.language.slug, region.default_language.slug
    ):
        client.send_message(
            zammad_chat.zammad_id,
            translation,
            True,
            True,
        )
    if answer := automatic_answer(message_text, region, zammad_chat.language.slug):
        client.send_message(
            zammad_chat.zammad_id,
            answer,
            False,
            True,
        )


@shared_task
def process_answer(message_text: str, region_slug: str, zammad_ticket_id: int) -> None:
    """
    Process automatic or counselor answers
    """
    zammad_chat = UserChat.objects.get(zammad_id=zammad_ticket_id)
    region = Region.objects.get(slug=region_slug)
    client = ZammadChatAPI(region)
    if translation := automatic_translation(
        message_text, region.default_language.slug, zammad_chat.language.slug
    ):
        client.send_message(
            zammad_chat.zammad_id,
            translation,
            False,
            True,
        )
