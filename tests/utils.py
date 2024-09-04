"""
This file contains helper functions for tests.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import TYPE_CHECKING

from django.db.models.signals import pre_save

from integreat_cms.cms.models import PageTranslation
from integreat_cms.core.signals.hix_signals import page_translation_save_handler

if TYPE_CHECKING:
    from typing import Generator

    from _pytest.logging import LogCaptureFixture


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
    assert (
        not error_messages
    ), "The following error messages were found in the message log:\n\n" + "\n".join(
        error_messages
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
