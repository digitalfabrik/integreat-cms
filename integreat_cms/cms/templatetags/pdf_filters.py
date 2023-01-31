"""
This is a collection of tags and filters for page content used in PDFs (:class:`~integreat_cms.cms.models.pages.page.Page`).
"""
import re
from html import unescape
from django import template
from lxml.html import fromstring, tostring
from lxml.etree import ParserError

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
        style = element.attrib.pop("style", None)
        if style:
            element.attrib["style"] = re.sub(r"font-[a-zA-Z]+:[^;]+", "", style)
    return unescape(tostring(content, with_tail=False).decode("utf-8"))
