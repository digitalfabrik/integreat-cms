from django.conf import settings

from linkcheck.models import Url


def filter_urls(url_filter=None):
    """
    Filter all urls of one region by the given category

    :param url_filter: which urls should be returned (one of ``valid``, ``invalid``, ``ignored``, ``unchecked``).
                        If parameter is not in these choices or omitted, all urls are returned by default.
    :type url_filter: str

    :return: A tuple of the requested urls and a dict containing the counters of all remaining urls
    :rtype: tuple
    """

    urls = [
        url
        for url in Url.objects.all().prefetch_related("links__content_object")
        if url.type not in settings.LINKCHECK_IGNORED_URL_TYPES
    ]

    # Split url lists into their respective categories
    ignored_urls, valid_urls, invalid_urls, unchecked_urls = [], [], [], []
    for url in urls:
        if all(link.ignore for link in url.links.all()):
            ignored_urls.append(url)
        elif url.status:
            valid_urls.append(url)
        elif url.last_checked:
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
