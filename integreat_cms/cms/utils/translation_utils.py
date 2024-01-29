"""
This module contains helpers for the gettext translation process of UI languages.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from django.utils.html import format_html, format_html_join
from django.utils.text import format_lazy

if TYPE_CHECKING:
    from typing import Any

    from django.utils.functional import Promise
    from django.utils.safestring import SafeString

logger = logging.getLogger(__name__)


def gettext_many_lazy(*strings: Any) -> Promise:
    r"""
    This function is a wrapper for :func:`django.utils.text.format_lazy` for the special case that the given strings
    should be concatenated with a space in between. This is useful for splitting lazy translated strings by sentences
    which improves the translation memory.

    :param \*strings: A list of lazy translated strings which should be concatenated
    :return: A lazy formatted string
    """
    fstring = ("{} " * len(strings)).strip()
    return format_lazy(fstring, *strings)


def translate_link(message: Promise | str, attributes: dict[str, str]) -> SafeString:
    """
    Translate a link with keeping the HTML tags and still escaping all unknown parts of the message

    :param message: The translated message that contains the link placeholder ``<a>{link_text}</a>``
    :param attributes: A dictionary of attributes for the link
    :return: A correctly escaped formatted string with the translated message and the HTML link
    """
    # Split the message at the link text
    before, link_text, after = re.split(r"<a>(.+)</a>", str(message))
    # Format the HTML
    return format_html(
        "{}<a {}>{}</a>{}",
        before,
        format_html_join(" ", "{}='{}'", attributes.items()),
        link_text,
        after,
    )
