"""
This is a collection of tags and filters for page content used in PDFs (:class:`~integreat_cms.cms.models.pages.page.Page`).
"""

from __future__ import annotations

import re
from html import unescape

from django import template
from django.utils.text import Truncator
from lxml.etree import ParserError
from lxml.html import fromstring, tostring

register = template.Library()


@register.filter
def pdf_strip_fontstyles(instance: str) -> str:
    """
    This tag returns the instance, stripped of inline styling affecting fonts.

    :param instance: The content object instance
    :return: The instance without inline font styling
    """
    try:
        content = fromstring(instance)
    except ParserError:
        return instance
    for element in content.iter():
        if style := element.attrib.pop("style", None):
            element.attrib["style"] = re.sub(r"font-[a-zA-Z]+:[^;]+", "", style)
    return unescape(tostring(content, encoding="unicode", with_tail=False))


@register.filter
# pylint: disable=unused-variable
def pdf_truncate_links(page_content: str, max_chars: int) -> str:
    """
    This tag returns the page content with truncated link texts.

    :param page_content: The content of the page
    :param max_chars: The maximal length of a link before it will be truncated
    :return: The content with truncated links
    """
    try:
        content = fromstring(page_content)
    except ParserError:
        return page_content
    for elem, attrib, link, pos in content.iterlinks():
        if elem.text:
            elem.text = " ".join(
                Truncator(word).chars(max_chars) for word in elem.text.split(" ")
            )

    return unescape(tostring(content, encoding="unicode", with_tail=False))
