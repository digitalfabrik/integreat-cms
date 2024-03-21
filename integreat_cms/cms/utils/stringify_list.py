from collections.abc import Iterable

from django.utils.translation import gettext_lazy as _


def iter_to_string(
    iterable: Iterable, *, quotation_char: str = '"', max_items: int = 5
) -> str:
    """
    This is a helper function that turns a list into a string using different delimiters.

    :param iterable: List of items
    :param quotation_char: The character that is added around each item in the list
    :param max_items: The maximum number of items in the iterable to display
    :return: Returns string with the single items separated by comma expect the last item which is separated by 'and'.
    """
    # Convert iterable to list to support querysets etc.
    elements = list(iterable)
    last_element_to_display = elements.pop() if 1 < len(elements) <= max_items else None
    # Join remaining elements with commas and surrounding quotes
    separator = quotation_char + ", " + quotation_char
    elements_str = (
        quotation_char + separator.join(map(str, elements[:max_items])) + quotation_char
    )

    # Handle the last element with 'and' and note that there are more elements if limited by `max_items`
    number_elements_over_limit = len(elements) - max_items
    if number_elements_over_limit == 1:
        elements_str += " " + _("and 1 other")
    elif number_elements_over_limit > 1:
        elements_str += " " + _("and {} others").format(number_elements_over_limit)
    elif last_element_to_display:
        elements_str += (
            " "
            + _("and")
            + f" {quotation_char}{last_element_to_display}{quotation_char}"
        )

    return elements_str
