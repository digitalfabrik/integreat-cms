"""
This is a collection of tags and filters for page content used in PDFs (:class:`~integreat_cms.cms.models.pages.page.Page`).
"""
import re
from html import unescape

from django import template
from django.utils.text import Truncator
from lxml.etree import ParserError
from lxml.html import fromstring, tostring

register = template.Library()


@register.filter
def pdf_strip_fontstyles(instance):
    """
    This tag returns the instance, stripped of inline styling affecting fonts.

    :param instance: The content object instance
    :type instance: ~integreat_cms.cms.models.pages.page.Page

    :return: The instance without inline font styling
    :rtype: ~integreat_cms.cms.models.pages.page.Page
    """
    try:
        content = fromstring(instance)
    except ParserError:
        return instance
    for element in content.iter():
        if style := element.attrib.pop("style", None):
            element.attrib["style"] = re.sub(r"font-[a-zA-Z]+:[^;]+", "", style)
    return unescape(tostring(content, with_tail=False).decode("utf-8"))


@register.filter
# pylint: disable=unused-variable
def pdf_truncate_links(page_content, max_chars):
    """
    This tag returns the page content with truncated link texts.

    :param page_content: The content of the page
    :type page_content: str

    :param max_chars: The maximal length of a link before it will be truncated
    :type max_chars: int

    :return: The content with truncated links
    :rtype: str
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

    return unescape(tostring(content, with_tail=False).decode("utf-8"))
