from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import parse_qsl, urlencode

from django.shortcuts import reverse

if TYPE_CHECKING:
    from django.http import HttpRequest


def get_filtered_events_url(
    request: HttpRequest, region_slug: str, language_slug: str
) -> str:
    """
    Build the events list URL, preserving any active filter query string from the request.

    :param request: The current HTTP request
    :param region_slug: Slug of the region
    :param language_slug: Current GUI language slug

    :return: The events list URL with optional filter query string
    """
    event_url = reverse(
        "events", kwargs={"region_slug": region_slug, "language_slug": language_slug}
    )
    if params := parse_qsl(request.POST.get("query_string", "")):
        event_url = f"{event_url}?{urlencode(params)}"
    return event_url
