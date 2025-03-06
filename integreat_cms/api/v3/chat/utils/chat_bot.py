"""
Wrapper for the Chat Bot / LLM API
"""

from __future__ import annotations

import asyncio

import aiohttp
from celery import shared_task
from django.conf import settings

from integreat_cms.cms.models import Region, UserChat

from .zammad_api import ZammadChatAPI


async def automatic_answer(
    messages: list,
    region_slug: str,
    language_slug: str,
    session: aiohttp.ClientSession,
) -> dict:
    """
    Get automatic answer to question asynchronously
    """
    url = (
        f"https://{settings.INTEGREAT_CHAT_BACK_END_DOMAIN}/chatanswers/extract_answer/"
    )
    body = {"messages": messages, "language": language_slug, "region": region_slug}
    async with session.post(
        url,
        json=body,
        timeout=settings.INTEGREAT_CHAT_BACK_END_TIMEOUT,
    ) as response:
        return await response.json()


async def automatic_translation(
    message: str,
    source_language_slug: str,
    target_language_slug: str,
    session: aiohttp.ClientSession,
) -> dict:
    """
    Use LLM to translate message asynchronously
    """
    url = f"https://{settings.INTEGREAT_CHAT_BACK_END_DOMAIN}/chatanswers/translate_message/"
    body = {
        "message": message,
        "source_language": source_language_slug,
        "target_language": target_language_slug,
    }
    async with session.post(
        url,
        json=body,
        timeout=settings.INTEGREAT_CHAT_BACK_END_TIMEOUT,
    ) as response:
        return await response.json()


async def async_process_user_message(
    zammad_chat_language_slug: str,
    region_slug: str,
    region_default_language_slug: str,
    messages: list[dict],
) -> tuple[dict, dict]:
    """
    Process the message from an Integreat App user
    """
    async with aiohttp.ClientSession() as session:
        translation_task = automatic_translation(
            messages[-1]["body"],
            zammad_chat_language_slug,
            region_default_language_slug,
            session,
        )
        answer_task = automatic_answer(
            messages,
            region_slug,
            zammad_chat_language_slug,
            session,
        )
        translation, answer = await asyncio.gather(translation_task, answer_task)
        return translation, answer


@shared_task
def process_user_message(
    region_slug: str,
    zammad_ticket_id: int,
) -> None:
    """
    Call the async processing of the message from an Integreat App user. The question
    should be translated into the main language and an automatic answer should be generated.
    """
    region = Region.objects.get(slug=region_slug)
    zammad_chat = UserChat.objects.get(zammad_id=zammad_ticket_id, region=region)
    client = ZammadChatAPI(region)
    messages = client.get_api_response(zammad_chat)["messages"]
    if not isinstance(messages, list):
        raise TypeError("Messages is are not a list")
    translation, answer = asyncio.run(
        async_process_user_message(
            zammad_chat.language.slug,
            region_slug,
            region.default_language.slug,
            messages,
        ),
    )
    if translation:
        client.send_message(
            zammad_chat,
            translation["translation"],
            True,
            True,
        )
    if answer:
        client.send_message(
            zammad_chat,
            answer["answer"],
            False,
            True,
            answer["automatic_answers"],
        )


async def async_process_translate(
    message_text: str,
    source_language: str,
    target_language: str,
) -> dict:
    """
    Process automatic or counselor answers
    """
    async with aiohttp.ClientSession() as session:
        translation_task = automatic_translation(
            message_text,
            source_language,
            target_language,
            session,
        )
        return await translation_task


@shared_task
def process_translate_answer(
    message_text: str, region_slug: str, zammad_ticket_id: int
) -> None:
    """
    Process automatic or counselor answers. These messages just need a translation.
    """
    region = Region.objects.get(slug=region_slug)
    zammad_chat = UserChat.objects.get(zammad_id=zammad_ticket_id, region=region)
    client = ZammadChatAPI(region)
    translation = asyncio.run(
        async_process_translate(
            message_text,
            region.default_language.slug,
            zammad_chat.language.slug,
        ),
    )
    if translation:
        client.send_message(
            zammad_chat,
            translation["translation"],
            False,
            True,
        )


@shared_task
def process_translate_question(
    message_text: str, region_slug: str, zammad_ticket_id: int
) -> None:
    """
    Process translation of app user questions
    """
    region = Region.objects.get(slug=region_slug)
    zammad_chat = UserChat.objects.get(zammad_id=zammad_ticket_id, region=region)
    client = ZammadChatAPI(region)
    translation = asyncio.run(
        async_process_translate(
            message_text, zammad_chat.language.slug, region.default_language.slug
        )
    )
    if translation:
        client.send_message(
            zammad_chat,
            translation["translation"],
            True,
            True,
        )
