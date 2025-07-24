"""
This file contains helper functions for tests.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import TYPE_CHECKING

from django.db.models.signals import pre_save
from lxml.html import fromstring, HtmlElement, tostring

from integreat_cms.cms.models import PageTranslation
from integreat_cms.core.signals.hix_signals import page_translation_save_handler

if TYPE_CHECKING:
    from collections.abc import Generator

    from _pytest.logging import LogCaptureFixture
    from django.http import HttpResponse


def get_messages(caplog: LogCaptureFixture) -> list[str]:
    """
    Get all logs from the messages framework

    :param caplog: The :fixture:`caplog` fixture
    :return: The list of messages that were shown to the user
    """
    message_log_matches = re.findall(
        r"^([A-Z]+[\s]+)integreat_cms.core.storages:storages.py:[\d]+ (.*)$",
        caplog.text,
        flags=re.MULTILINE,
    )
    return [level + message for level, message in message_log_matches]


def get_error_messages(caplog: LogCaptureFixture) -> list[str]:
    """
    Get all errors from the messages framework

    :param caplog: The :fixture:`caplog` fixture
    :return: The list of error messages that were shown to the user
    """
    return [message for message in get_messages(caplog) if message.startswith("ERROR ")]


def assert_no_error_messages(caplog: LogCaptureFixture) -> None:
    """
    Assert that no error messages were shown to the user

    :param caplog: The :fixture:`caplog` fixture
    :raises AssertionError: When the the logs contains error messages
    """
    error_messages = get_error_messages(caplog)
    assert not error_messages, (
        "The following error messages were found in the message log:\n\n"
        + "\n".join(error_messages)
    )


def assert_message_in_log(message: str, caplog: LogCaptureFixture) -> None:
    """
    Check whether a given message is in the messages div

    :param message: The expected message
    :param caplog: The :fixture:`caplog` fixture
    :raises AssertionError: When the expected message was not found in the logs
    """
    messages = get_messages(caplog)
    assert message in messages, (
        f"The following message: \n\n{message}\n\nwas not found in the message log:\n\n"
        + ("\n".join(messages) if messages else "empty message log.")
    )


@contextmanager
def disable_hix_post_save_signal() -> Generator[None, None, None]:
    pre_save.disconnect(receiver=page_translation_save_handler, sender=PageTranslation)
    try:
        yield None
    finally:
        pre_save.connect(receiver=page_translation_save_handler, sender=PageTranslation)


def get_messages_in_html(response: HttpResponse) -> str:
    """
    Filter the response content for the div with ``id="messages"``
    ànd return its HTML with any superfluous whitespace stripped out.
    """
    content = response.content.decode("utf-8")
    doc = fromstring(content)
    matches = doc.xpath("//div[@id='messages']")

    def strip_whitespace(element: HtmlElement) -> HtmlElement:
        if element.text is not None:
            element.text = element.text.strip()
        if element.tail is not None:
            element.tail = element.tail.strip()
        for child in element:
            strip_whitespace(child)
        return element

    # Technically there might be multiple divs with the id,
    # so we just join the string representation of all of them together
    return "".join(
        [
            tostring(strip_whitespace(messages), encoding="unicode")
            for messages in matches
        ]
    )
