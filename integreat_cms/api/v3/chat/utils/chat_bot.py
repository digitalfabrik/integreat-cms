"""
Wrapper for the Chat Bot / LLM API
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import aiohttp
from celery import shared_task
from django.conf import settings

from integreat_cms.cms.models import Region, UserChat


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

    :param zammad_chat_language_slug: Language selected in Integreat App
    :param region_slug: region used in webhook
    :param region_default_language_slug: default language of region / counselors
    :param messages: list of all messages (can contain newer messages than message_text)
    """
    async with aiohttp.ClientSession() as session:
        translation_task = automatic_translation(
            messages[-1]["content"],
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
    message_timestamp: datetime,
    region_slug: str,
    zammad_ticket_id: int,
) -> None:
    """
    Call the async processing of the message from an Integreat App user. The question
    should be translated into the main language and an automatic answer should be generated.

    :param message_timestamp: Timestamp of the article that triggered the webhook
    :param region_slug: region used in webhook
    :param zammad_ticket_id: Ticket ID contained in webhook request
    """
    region = Region.objects.get(slug=region_slug)
    zammad_chat = UserChat.objects.get(zammad_id=zammad_ticket_id, region=region)
    translation, answer = asyncio.run(
        async_process_user_message(
            zammad_chat.language.slug,
            region_slug,
            region.default_language.slug,
            # Prevent a race condition where new articles can be added to a ticket
            # while the webhook has not yet sent to and processed by the Integreat CMS
            [
                message
                for message in zammad_chat.messages
                if datetime.fromisoformat(message["created_at"]) <= message_timestamp
            ],
        ),
    )
    if translation:
        zammad_chat.save_message(
            message=translation["translation"],
            internal=True,
            automatic_message=True,
        )
    if answer:
        zammad_chat.save_message(
            message=answer["answer"],
            internal=False,
            automatic_message=True,
        )
        zammad_chat.save_automatic_answers(answer["automatic_answers"])


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
    translation = asyncio.run(
        async_process_translate(
            message_text,
            region.default_language.slug,
            zammad_chat.language.slug,
        ),
    )
    if translation:
        zammad_chat.save_message(
            message=translation["translation"],
            internal=False,
            automatic_message=True,
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
    translation = asyncio.run(
        async_process_translate(
            message_text, zammad_chat.language.slug, region.default_language.slug
        )
    )
    if translation:
        zammad_chat.send_message(
            message=translation["translation"],
            internal=True,
            automatic_message=True,
        )
