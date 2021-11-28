"""
This module contains helpers for the translation process.
"""
from django.utils.text import format_lazy


def ugettext_many_lazy(*strings):
    r"""
    This function is a wrapper for :func:`django.utils.text.format_lazy` for the special case that the given strings
    should be concatenated with a space in between. This is useful for splitting lazy translated strings by sentences
    which improves the translation memory.

    :param \*strings: A list of lazy translated strings which should be concatenated
    :type \*strings: list

    :return: A lazy formatted string
    :rtype: str
    """
    fstring = ("{} " * len(strings)).strip()
    return format_lazy(fstring, *strings)
