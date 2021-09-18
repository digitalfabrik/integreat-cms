"""
This is a collection of tags and filters which are useful for all user forms
"""
import logging

from django import template

logger = logging.getLogger(__name__)
register = template.Library()


@register.filter
def remaining_regions(user, region_to_remove):
    """
    This calculates the remaining regions of a user after a given region is removed

    :param user: The given user
    :type user: ~django.contrib.auth.models.User

    :param region_to_remove: The region which should be removed from the user's regions
    :type region_to_remove:  ~integreat_cms.cms.models.regions.region.Region

    :return: The Queryset of regions
    :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.regions.region.Region ]
    """
    return user.regions.exclude(slug=region_to_remove.slug)
