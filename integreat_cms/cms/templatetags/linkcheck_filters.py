from __future__ import annotations

from typing import TYPE_CHECKING

from django import template
from django.utils.safestring import mark_safe

if TYPE_CHECKING:
    from linkcheck.models import Url

register = template.Library()


@register.simple_tag
@mark_safe
def url_ssl_icon(url: Url) -> str:
    """
    Return the icon that represents an URL's SSL status

    :param url: The URL
    :return: The HTML code of the SSL status icon
    """
    if url.internal:
        return ""
    if url.external_url.startswith("http://"):
        return '<i icon-name="shield-off" class="text-red-500"></i>'
    if url.ssl_status is None:
        return '<i icon-name="lock"></i>'
    if url.ssl_status is False:
        return '<i icon-name="unlock" class="text-red-500"></i>'
    return '<i icon-name="lock" class="text-green-500"></i>'


@register.simple_tag
@mark_safe
def url_anchor_icon(url: Url) -> str:
    """
    Return the icon that represents an URL's HTML anchor status

    :param url: The URL
    :return: The HTML code of the anchor status icon
    """
    if not url.has_anchor or not url.last_checked:
        return ""
    if not url.anchor:
        return '<i icon-name="check" class="text-green-500"></i>'
    if url.anchor_status is None:
        return '<i icon-name="help-circle" class="text-green-500"></i>'
    if url.anchor_status is False:
        return '<i icon-name="x" class="text-red-500"></i>'
    return '<i icon-name="check" class="text-green-500"></i>'
