from django import template

register = template.Library()


@register.filter
def diff(value: int, arg: int) -> int:
    """subtract arg from value

    :param value: origin value
    :param arg: value to be subtracted
    :return: result of subtraction
    """
    return value - arg
