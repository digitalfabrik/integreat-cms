"""
This module includes functions related to the social media headers API endpoint.
"""
from __future__ import annotations

import logging
from html import unescape
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils.html import strip_tags
from django.utils.translation import activate

from integreat_cms.cms.models.events.event_translation import EventTranslation
from integreat_cms.cms.models.languages.language import Language
from integreat_cms.cms.models.pois.poi_translation import POITranslation
from integreat_cms.cms.models.push_notifications.push_notification_translation import (
    PushNotificationTranslation,
)
from integreat_cms.cms.models.regions.region import Region

from ...cms.models import PageTranslation

if TYPE_CHECKING:
    from typing import Optional

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


def socialmedia_headers(
    request: HttpRequest, path: Optional[str] = None
) -> HttpResponse:
    """
    Detects the path context and renders the socialmedia headers.
    Available contexts are:
    - root e.g. /, /landing, /disclaimer, /landing/de
    - region root e.g. /testumgebung, /testumgebung/de, /testumgebung/de/events
    - page e.g. /testumgebung/de/willkommen, /testumgebung/de/events/event

    :param request: The request that has been sent to the Django server
    :param path: The path of the page the social meddia headers should be created for

    :return: HTML meta headers required by social media platforms
    """
    slugs = list(filter(bool, path.split("/"))) if path else []

    potential_region_slug = slugs[0] if len(slugs) > 0 else None
    region = (
        Region.objects.filter(slug=potential_region_slug).first()
        if potential_region_slug
        else None
    )

    potential_language_slug = slugs[1] if len(slugs) > 1 else None
    language = Language.objects.filter(
        slug=potential_language_slug
    ).first() or Language.objects.get(slug="de")
    if not region:
        return root_socialmedia_headers(request, language, path or "")

    if len(slugs) < 3:
        return region_socialmedia_headers(request, region, path or "")

    return page_socialmedia_headers(request, region, language, "/".join(slugs[2:]))


def root_socialmedia_headers(
    request: HttpRequest, language: Language, path: str
) -> HttpResponse:
    """
    Renders the socialmedia headers for a root page

    :param request: The request that has been sent to the django server
    :param language: The language of the page
    :param path: The path to the page

    """
    title = language.socialmedia_webapp_title
    url = f"{settings.WEBAPP_URL}/{path}"

    excerpt = (
        (
            "hallo aschaffenburg is your digital companion for the town of Aschaffenburg. Here"
            " you can find local information, advice centres and services."
        )
        if settings.BRANDING == "aschaffenburg"
        else (
            settings.BRANDING_TITLE + " is your digital companion for Germany. Here"
            " you can find local information, advice centres and services."
        )
    )
    return render_socialmedia_headers(request, title, excerpt, url)


def region_socialmedia_headers(
    request: HttpRequest, region: Region, path: str
) -> HttpResponse:
    """
    Renders the social media headers for a root region page

    :param request: The request that has been sent to the Django Server
    :param region: The region the request refers to
    :param path: The path to the page
    """
    title = f"{region.name} | {settings.BRANDING_TITLE}"
    url = f"{settings.WEBAPP_URL}/{path}"
    return render_socialmedia_headers(request, title, None, url)


def page_socialmedia_headers(
    request: HttpRequest, region: Region, language: Language, path: str
) -> HttpResponse:
    """
    Renders the social media headers for a single page

    :param request: The request that has been sent to the Django server
    :param region: The region the page belongs to
    :param language: Language of the page
    :param path: Should be a page translation slug
    :return: HTML meta headers required by social media platforms
    """

    route, *route_path = path.split("/", maxsplit=1)

    if route == "events" and len(route_path):
        # TODO: add event json-ld
        content_translation = EventTranslation.search(
            region, language.slug, *route_path
        ).first()
    elif route == "locations" and len(route_path):
        content_translation = POITranslation.search(
            region, language.slug, *route_path
        ).first()
    elif route == "news" and len(route_path):
        content_translation = PushNotificationTranslation.search(
            region, language.slug, *route_path
        ).first()
    else:
        # TODO: add breadcrumb json-ld if content_translation exists
        content_translation = PageTranslation.search(
            region, language.slug, path
        ).first()

        if not content_translation:
            # not a "page"-route e.g. /imprint, /events
            return region_socialmedia_headers(request, region, path)

    activate(language.slug)

    if not content_translation:
        raise Http404

    excerpt = unescape(strip_tags(content_translation.content))[:100]
    title = f"{content_translation.title} - {region.name} | {settings.BRANDING_TITLE}"
    return render_socialmedia_headers(
        request, title, excerpt, content_translation.full_url
    )


def render_socialmedia_headers(
    request: HttpRequest, title: str, excerpt: Optional[str], url: str
) -> HttpResponse:
    """
    Renders the socialmedia headers with the specified arguments

    :param request: The request sent to the Django Server
    :param title: The title of the page in the socialmedia headers
    :param excerpt: An optional excerpt describing the content of the page. If omitted google, will automatically crawl an excerpt
    :param url: The url the headers belong to
    """
    return render(
        request,
        "socialmedia_headers.html",
        {
            "title": title,
            "excerpt": excerpt,
            "platform": settings.BRANDING_TITLE,
            "url": url,
            "image": settings.SOCIAL_PREVIEW_IMAGE,
        },
    )
