"""
This contains tags for accessing settings
"""
from django.conf import settings
from django import template


register = template.Library()


@register.simple_tag
def get_webapp_url():
    """
    This tag returns the ``WEBAPP_URL``

    :return: The url of the current web application
    :rtype: str
    """
    return settings.WEBAPP_URL


@register.simple_tag
def get_base_url():
    """
    This tag returns the ``BASE_URL``

    :return: The base url of the current web application
    :rtype: str
    """
    return settings.BASE_URL
