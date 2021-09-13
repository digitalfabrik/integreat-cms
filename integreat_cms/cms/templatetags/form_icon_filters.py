import os

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def strip_path(icon):
    """
    strips the internal path of the icon file to show user only the file name

    :param icon: relative path inside the media folder
    :type icon: str
    :return: name of icon file
    :rtype: str
    """
    return os.path.basename(icon)
