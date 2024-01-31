"""
This module contains helpers for strings.
"""

from __future__ import annotations

from django.utils.functional import keep_lazy_text, Promise


@keep_lazy_text
def lowfirst(string: Promise) -> str:
    """
    Make the first letter of a string lowercase (counterpart of :func:`~django.utils.text.capfirst`, see also
    :templatefilter:`capfirst`).

    :param string: The input text
    :return: The lowercase text
    """
    return string and str(string)[0].lower() + str(string)[1:]


def truncate_bytewise(string: str, length: int) -> str:
    """
    Truncate a UTF-8 encoded string to a maximum byte length.

    :param string: The input text
    :param length: The maximum length of the text in byte representation
    :return: The truncated text
    """
    encoded_string = string.encode()
    try:
        return encoded_string[:length].decode()
    except UnicodeDecodeError as e:
        return encoded_string[: e.start].decode()
