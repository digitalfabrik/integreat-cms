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


def truncate_bytewise(string, length):
    """
    Truncate a UTF-8 encoded string to a maximum byte length.

    :param string: The input text
    :type string: str

    :param length: The maximum length of the text in byte representation
    :type length: int

    :return: The truncated text
    :rtype: str
    """
    encoded_string = string.encode()
    try:
        return encoded_string[:length].decode()
    except UnicodeDecodeError as e:
        return encoded_string[: e.start].decode()
