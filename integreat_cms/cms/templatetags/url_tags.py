"""
Contains a collection of tags for working with urls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

if TYPE_CHECKING:
    from typing import Any
    from urllib.parse import ParseResult

    from django.http import HttpRequest

register = template.Library()


@register.simple_tag
def add_queries(url: str, key: str, value: str | int) -> str:
    """
    This filter adds a query to an url

    :param url: The url to modify
    :param key: The key of the querystring
    :param value: The value of the querystring

    :return: The url with a modified query part
    """
    parsed_url: ParseResult = urlparse(url)
    url_query: dict[str, list[str]] = parse_qs(parsed_url.query, keep_blank_values=True)
    url_query[key] = [str(value)]

    parsed_url = parsed_url._replace(query=urlencode(url_query, doseq=True))
    return urlunparse(parsed_url)


@register.simple_tag
@mark_safe
def url_for_current_region(target: str, request: HttpRequest, **kwargs: Any) -> str:
    """
    Return the url matching the target url name, region and other supplied slugs

    :param target: The name of target url
    :param request: The current request, used to check whether a region is given or not
    :param kwargs: Other slugs passed as the keyword argument
    """
    if request.region:
        kwargs["region_slug"] = request.region.slug
    return reverse(target, kwargs=kwargs)
