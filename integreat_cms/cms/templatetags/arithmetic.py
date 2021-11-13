from django import template

register = template.Library()


@register.filter
def diff(value, arg):
    """subtract arg from value

    :param value: origin value
    :type value: int
    :param arg: value to be subtracted
    :type arg: int
    :return: result of subtraction
    :rtype: int
    """
    return value - arg
