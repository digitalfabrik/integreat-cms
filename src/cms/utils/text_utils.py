"""
This module contains helpers for strings.
"""
from django.utils.functional import keep_lazy_text


@keep_lazy_text
def lowfirst(string):
    """
    Make the first letter of a string lowercase (counterpart of :func:`~django.utils.text.capfirst`, see also
    :templatefilter:`capfirst`).

    :param string: The input text
    :type string: str

    :return: The lowercase text
    :rtype: str
    """
    return string and str(string)[0].lower() + str(string)[1:]
