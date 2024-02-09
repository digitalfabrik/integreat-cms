"""
This is a collection of tags and filters which are useful for all user forms
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from django.db.models.query import QuerySet

    from ..models import Region, User

logger = logging.getLogger(__name__)
register = template.Library()


@register.filter
def remaining_regions(user: User, region_to_remove: Region) -> QuerySet[Region]:
    """
    This calculates the remaining regions of a user after a given region is removed

    :param user: The given user
    :param region_to_remove: The region which should be removed from the user's regions
    :return: The Queryset of regions
    """
    return user.regions.exclude(slug=region_to_remove.slug)
