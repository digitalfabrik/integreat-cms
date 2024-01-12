from django.utils.translation import gettext_lazy as _


def iter_to_string(iterable: list) -> str:
    """
    This is a helper function that turns a list into a string using different delimiters.

    :param iterable: List of items
    :return: Returns string with the single items separated by comma expect the last item which is separated by 'and'.
    """
    # Convert iterable to list to support querysets etc.
    lst = list(iterable)
    # If the list contains more than 1 element, save the last element for later
    last_element = lst.pop() if len(lst) > 1 else None
    # Join remaining elements with commas and surrounding quotes
    list_str = '"' + '", "'.join(map(str, lst)) + '"'
    # Append the last element with "and"
    if last_element:
        list_str += " " + _("and") + f' "{last_element}"'
    # Return final string
    return list_str
