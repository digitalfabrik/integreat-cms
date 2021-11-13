from django import template

register = template.Library()


@register.filter
def in_list(value, comma_separated_list):
    """
    This tag checks whether a given string value is contained in a comma separated list

    :param value: The value which should be checked
    :type value: str

    :param comma_separated_list: The list of comma-separated strings
    :type comma_separated_list: str

    :return: Whether or not value is contained in the list
    :rtype: bool
    """
    return value in comma_separated_list.split(",")
