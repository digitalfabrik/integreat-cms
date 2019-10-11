from django import template

register = template.Library()


@register.filter
def active_since(region_extras, extra_template):
    return region_extras.filter(template=extra_template).first().created_date
