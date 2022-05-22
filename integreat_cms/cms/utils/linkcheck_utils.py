from django.conf import settings
from django.db.models import Prefetch, Q

from linkcheck.models import Url, Link


def get_urls(region_slug=None, url_ids=None, prefetch_content_objects=True):
    """
    Count all urls by status, either of a specific region or globally

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param url_ids: The list of requested url ids
    :type url_ids: list

    :param prefetch_content_objects: Whether or not content objects should be prefetched
    :type prefetch_content_objects: bool

    :return: The list (or queryset) of urls
    :rtype: list or ~django.db.models.query.QuerySet
    """
    urls = Url.objects.all()
    if url_ids is not None:
        # If the results should be limited to specific ids, filter the queryset
        urls = urls.filter(id__in=url_ids)
    if region_slug:
        # Get all link objects of the requested region
        region_links = Link.objects.filter(
            Q(page_translation__page__region__slug=region_slug)
            | Q(imprint_translation__page__region__slug=region_slug)
            | Q(event_translation__event__region__slug=region_slug)
            | Q(poi_translation__poi__region__slug=region_slug)
        )
        if prefetch_content_objects:
            region_links = region_links.prefetch_related("content_object")
        # Prefetch all link objects of the requested region
        urls = urls.prefetch_related(
            Prefetch(
                "links",
                queryset=region_links,
                to_attr="region_links",
            )
        )
    elif prefetch_content_objects:
        urls = urls.prefetch_related("links__content_object")
    # Filter out ignored URL types
    urls = [url for url in urls if url.type not in settings.LINKCHECK_IGNORED_URL_TYPES]
    if region_slug:
        # If the region slug is given, only return urls that occur at least once in the requested region
        urls = [url for url in urls if url.region_links]
    return urls


def get_url_count(region_slug=None):
    """
    Count all urls by status. The content objects are not prefetched because they are not needed for the counter.

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: A dictionary containing the counters of all remaining urls
    :rtype: dict
    """
    _, count_dict = filter_urls(region_slug=region_slug, prefetch_content_objects=False)
    return count_dict


def filter_urls(region_slug=None, url_filter=None, prefetch_content_objects=True):
    """
    Filter all urls of one region by the given category

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param url_filter: Which urls should be returned (one of ``valid``, ``invalid``, ``ignored``, ``unchecked``).
                        If parameter is not in these choices or omitted, all urls are returned by default.
    :type url_filter: str

    :param prefetch_content_objects: Whether or not content objects should be prefetched
    :type prefetch_content_objects: bool

    :return: A tuple of the requested urls and a dict containing the counters of all remaining urls
    :rtype: tuple
    """
    urls = get_urls(
        region_slug=region_slug, prefetch_content_objects=prefetch_content_objects
    )
    # Split url lists into their respective categories
    ignored_urls, valid_urls, invalid_urls, unchecked_urls = [], [], [], []
    for url in urls:
        links = url.region_links if region_slug else url.links.all()
        if all(link.ignore for link in links):
            ignored_urls.append(url)
        elif url.status:
            valid_urls.append(url)
        elif url.status is False:
            # Explicitly check for False, because status is None means unchecked
            invalid_urls.append(url)
        else:
            unchecked_urls.append(url)
    # Pass the number of urls to a dict which can be used as extra template context
    count_dict = {
        "number_all_urls": len(urls),
        "number_valid_urls": len(valid_urls),
        "number_unchecked_urls": len(unchecked_urls),
        "number_ignored_urls": len(ignored_urls),
        "number_invalid_urls": len(invalid_urls),
    }
    # Return the requested urls
    if url_filter == "valid":
        urls = valid_urls
    elif url_filter == "unchecked":
        urls = unchecked_urls
    elif url_filter == "ignored":
        urls = ignored_urls
    elif url_filter == "invalid":
        urls = invalid_urls

    return urls, count_dict
