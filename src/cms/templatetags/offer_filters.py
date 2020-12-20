"""
This is a collection of tags and filters for :class:`~cms.models.offers.offer.Offer` objects.
"""
from django import template

register = template.Library()


@register.filter
def active_since(region_offers, offer_template):
    """
    This filter returns the date when a specific offer template was activated for the given region.

    :param region_offers: The offer objects of a given region
    :type region_offers: ~django.db.models.query.QuerySet [ ~cms.models.offers.offer.Offer ]

    :param offer_template: The requested offer template
    :type offer_template: ~cms.models.offers.offer_template.OfferTemplate

    :return: The date and time when the offer was activated
    :rtype: ~datetime.datetime
    """
    return region_offers.filter(template=offer_template).first().created_date
