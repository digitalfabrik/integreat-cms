"""
This module contains helpers for rendering social media meta headers.
"""

from __future__ import annotations

import re
from html import unescape
from typing import TYPE_CHECKING

from django.conf import settings
from django.shortcuts import render
from django.utils.html import strip_tags

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

    from ..models.regions.region import Region


def get_excerpt(content: str) -> str:
    """
    Correctly escapes, truncates and normalizes the content of the page to display in a search result.

    :param content: The content of the page

    :return: A page excerpt containing the first 100 characters of "raw" content
    """
    stripped_content = re.sub(
        r"\s+",
        " ",
        unescape(
            strip_tags(
                content.replace("\n", " ").replace("\r", "").replace("<br>", " ")
            )
        ),
    ).strip()
    if len(stripped_content) <= 100:
        return stripped_content
    return stripped_content[:100].rsplit(" ", 1)[0] + " …"


def get_region_title(region: Region, page_title: str) -> str:
    """
    Constructs in a unified format the page title of a page in a region.

    :param region: The region where the page resides in
    :param page_title: The title of the page

    :return: The constructed page title
    """
    return f"{page_title} - {region.name} | {settings.BRANDING_TITLE}"


def render_social_media_headers(
    request: HttpRequest,
    title: str,
    language_code: str,
    excerpt: str | None,
    url: str,
) -> HttpResponse:
    """
    Renders the social media headers with the specified arguments

    :param request: The current request
    :param title: The title of the page in the social media headers
    :param language_code: The language of the requested resource
    :param excerpt: An optional excerpt describing the content of the page. If omitted google, will automatically crawl an excerpt
    :param url: The url the headers belong to

    :return: HTML social meta headers required by social media platforms
    """
    return render(
        request,
        "social_media_headers.html",
        {
            "site_name": f"{settings.BRANDING_TITLE}",
            "title": title,
            "excerpt": excerpt,
            "url": url,
            "image": f"{settings.BASE_URL}/{settings.SOCIAL_PREVIEW_IMAGE}",
            "language_code": language_code,
        },
    )
