from django import template

register = template.Library()


@register.filter
def active_since(region_offers, offer_template):
    return region_offers.filter(template=offer_template).first().created_date
