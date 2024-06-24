from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def tagifnotempty(value, args):
    value = value.strip()
    return f'{str(args)}="{value}"' if value else value
