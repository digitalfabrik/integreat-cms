"""
This is a collection of tags and filters for strings.
"""
import json

from django import template
from django.utils.translation import ugettext as _

register = template.Library()


@register.filter(name="words")
def words(text):
    """
    Split the given text into a list of words, see :meth:`python:str.split`.

    :param text: The input string
    :type text: str

    :return: The list of words in the text
    :rtype: list
    """
    return text.split()


@register.filter(name="linkcheck_status_filter")
def linkcheck_status_filter(status_message):
    """
    Due to a long status entry for a single kind of faulty link,
    this filter reduced the output when display in list view

    :param status_message: error description
    :type status_message: str
    :return: a concise message
    :rtype: str
    """
    if not status_message:
        return _("Unknown")
    if status_message.startswith("Other Error:"):
        return _("Error")
    # Sometimes 404 errors are malformed
    if status_message in ["404 ", "404 404"]:
        return "404 Not Found"
    return _(status_message)


@register.filter(name="to_json")
def to_json(obj):
    """
    Converts the given object to a json string

    :param obj: The input object
    :type obj: object

    :return: object as json string
    :rtype: str
    """
    return json.dumps(obj)
