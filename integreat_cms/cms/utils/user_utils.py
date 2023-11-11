from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db.models import Q

if TYPE_CHECKING:
    from django.db.models.query import QuerySet

    from ..models import Region, User


def search_users(region: Region | None, query: str) -> QuerySet[User]:
    """
    Searches for all users that match the given `query`.
    If region is None, all users are searched.
    :param region: The current region
    :param query: The query string used for filtering the regions
    :return: A query for all matching objects
    """

    filter_query = (
        Q(username__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
    )

    objects = region.region_users if region else get_user_model().objects
    return objects.filter(filter_query)
