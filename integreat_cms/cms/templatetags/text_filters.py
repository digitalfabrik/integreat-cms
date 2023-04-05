"""
This is a collection of tags and filters for strings.
"""
import json

from django import template

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
