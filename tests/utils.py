"""
This file contains helper functions for tests.
"""
import re


def get_messages(caplog):
    """
    Get all logs from the messages framework

    :param caplog: The :fixture:`caplog` fixture
    :type caplog: pytest.LogCaptureFixture

    :return: The list of messages that were shown to the user
    :rtype: list[str]
    """
    message_log_matches = re.findall(
        r"^([A-Z]+[\s]+)integreat_cms.core.storages:storages.py:[\d]+ (.*)$",
        caplog.text,
        flags=re.MULTILINE,
    )
    return [level + message for level, message in message_log_matches]


def get_error_messages(caplog):
    """
    Get all errors from the messages framework

    :param caplog: The :fixture:`caplog` fixture
    :type caplog: pytest.LogCaptureFixture

    :return: The list of error messages that were shown to the user
    :rtype: list[str]
    """
    return [message for message in get_messages(caplog) if message.startswith("ERROR ")]


def assert_no_error_messages(caplog):
    """
    Assert that no error messages were shown to the user

    :param caplog: The :fixture:`caplog` fixture
    :type caplog: pytest.LogCaptureFixture

    :raises AssertionError: When the the logs contains error messages
    """
    error_messages = get_error_messages(caplog)
    assert (
        not error_messages
    ), "The following error messages were found in the message log:\n\n" + "\n".join(
        error_messages
    )


def assert_message_in_log(message, caplog):
    """
    Check whether a given message is in the messages div

    :param message: The expected message
    :type message: str

    :param caplog: The :fixture:`caplog` fixture
    :type caplog: pytest.LogCaptureFixture

    :raises AssertionError: When the expected message was not found in the logs
    """
    messages = get_messages(caplog)
    assert (
        message in messages
    ), f"The following message: \n\n{message}\n\nwas not found in the " + (
        "message log:\n\n" + "\n".join(messages) if messages else "empty message log."
    )
