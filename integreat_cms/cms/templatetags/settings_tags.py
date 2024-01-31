"""
This contains tags for accessing settings
"""

from __future__ import annotations

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_webapp_url() -> str:
    """
    This tag returns the ``WEBAPP_URL``

    :return: The url of the current web application
    """
    return settings.WEBAPP_URL


@register.simple_tag
def get_base_url() -> str:
    """
    This tag returns the ``BASE_URL``

    :return: The base url of the current web application
    """
    return settings.BASE_URL
