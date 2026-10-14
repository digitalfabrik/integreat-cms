"""
This module contains helpers for strings.
"""

from __future__ import annotations

import re
from html import unescape

from django.utils.functional import keep_lazy_text, Promise
from django.utils.html import strip_tags


STRUCTURAL_HTML_TAGS = r"(?:br|/?p|/?div|/?li|/?h[1-6])"


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


def strip_html_with_whitespace(content: str) -> str:
    """
    Remove HTML while retaining word boundaries represented by structural tags.

    :param content: The HTML content to convert to plain text
    :return: Normalized plain text without HTML tags
    """
    content_with_separators = re.sub(
        rf"<{STRUCTURAL_HTML_TAGS}\b[^>]*>",
        " ",
        content,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", unescape(strip_tags(content_with_separators))).strip()
