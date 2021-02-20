"""
This is a collection of tags and filters for strings.
"""
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
