from django.contrib.auth import get_user_model
from django.db.models import Q


def search_users(region, query):
    """
    Searches for all users that match the given `query`.
    If region is None, all users are searched.
    :param region: The current region
    :type region: ~integreat_cms.cms.models.regions.region.Region
    :param query: The query string used for filtering the regions
    :type query: str
    :return: A query for all matching objects
    :rtype: ~django.db.models.QuerySet
    """

    filter_query = (
        Q(username__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
    )

    if region:
        objects = region.users
    else:
        objects = get_user_model().objects

    return objects.filter(filter_query)
