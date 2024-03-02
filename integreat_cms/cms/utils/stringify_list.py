from collections.abc import Iterable

from django.utils.translation import gettext_lazy as _


def iter_to_string(iterable: Iterable, *, quotation_char: str = '"') -> str:
    """
    This is a helper function that turns a list into a string using different delimiters.

    :param iterable: List of items
    :param quotation_char: The character that is added around each item in the list
    :return: Returns string with the single items separated by comma expect the last item which is separated by 'and'.
    """
    # Convert iterable to list to support querysets etc.
    lst = list(iterable)
    # If the list contains more than 1 element, save the last element for later
    last_element = lst.pop() if len(lst) > 1 else None
    # Join remaining elements with commas and surrounding quotes
    separator = quotation_char + ", " + quotation_char
    list_str = quotation_char + separator.join(map(str, lst)) + quotation_char
    # Append the last element with "and"
    if last_element:
        list_str += " " + _("and") + f" {quotation_char}{last_element}{quotation_char}"
    # Return final string
    return list_str
