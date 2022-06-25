"""
Contains a collection of tags for working with urls.
"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from django import template


register = template.Library()


@register.simple_tag
def add_queries(url, *queries):
    r"""
    This filter adds a query to an url

    :param url: The url to modify
    :type url: str

    :param \*queries: The queries to add to the url. Should contain key-value pairs
    :type \*queries: tuple

    :return: The url with a modified query part
    :rtype: str
    """
    url = urlparse(url)
    url_query = parse_qs(url.query, keep_blank_values=True)
    while queries:
        key, value, *queries = queries
        url_query[key] = str(value)

    url = url._replace(query=urlencode(url_query, doseq=True))
    return urlunparse(url)
