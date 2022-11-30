"""
This module contains helpers for the translation process.
"""
import re

from django.utils.html import format_html, format_html_join
from django.utils.text import format_lazy


def gettext_many_lazy(*strings):
    r"""
    This function is a wrapper for :func:`django.utils.text.format_lazy` for the special case that the given strings
    should be concatenated with a space in between. This is useful for splitting lazy translated strings by sentences
    which improves the translation memory.

    :param \*strings: A list of lazy translated strings which should be concatenated
    :type \*strings: list

    :return: A lazy formatted string
    :rtype: str
    """
    fstring = ("{} " * len(strings)).strip()
    return format_lazy(fstring, *strings)


def translate_link(message, attributes):
    """
    Translate a link with keeping the HTML tags and still escaping all unknown parts of the message

    :param message: The translated message that contains the link placeholder ``<a>{link_text}</a>``
    :type message: str

    :param attributes: A dictionary of attributes for the link
    :type attributes: dict

    :return: A correctly escaped formatted string with the translated message and the HTML link
    :rtype: str
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
