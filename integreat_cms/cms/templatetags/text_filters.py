"""
This is a collection of tags and filters for strings.
"""

from __future__ import annotations

import json

from django import template

register = template.Library()


@register.filter(name="words")
def words(text: str) -> list[str]:
    """
    Split the given text into a list of words, see :meth:`python:str.split`.

    :param text: The input string
    :return: The list of words in the text
    """
    return text.split()


@register.filter(name="to_json")
def to_json(obj: tuple[int | str, str]) -> str:
    """
    Converts the given object to a json string

    :param obj: The input object
    :return: object as json string
    """
    return json.dumps(obj)
