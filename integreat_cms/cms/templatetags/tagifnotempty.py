from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeString

register = template.Library()


@register.filter
@stringfilter
def tagifnotempty(value: SafeString, args: SafeString) -> str:
    """
    Helper function for template to display property if it's not left empty
    :param value: url where that is being investigated
    :param args: properties that might be left empty
    :return: Correctly formatted properties
    """
    value = value.strip()
    return f'{str(args)}="{value}"' if value else value
