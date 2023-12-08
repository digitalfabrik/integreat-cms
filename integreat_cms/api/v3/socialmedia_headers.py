"""
This module includes functions related to the social media headers API endpoint.
"""
from __future__ import annotations

import logging
from html import unescape
from typing import TYPE_CHECKING

from django.conf import settings
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

    potential_language = (
        Language.objects.filter(slug=slugs[1]).first() if len(slugs) > 1 else None
    )
    language = potential_language or Language.objects.get(slug="de")
    if not region:
        return root_socialmedia_headers(request, language, path or "")

    content_headers = None
    if len(slugs) >= 3:
        content_headers = content_socialmedia_headers(
            request, region, language, "/".join(slugs[2:])
        )

    return (
        content_headers
        if content_headers
        else region_socialmedia_headers(request, region, path or "")
    )


def root_socialmedia_headers(
    request: HttpRequest, language: Language, path: str
) -> HttpResponse:
    """
    Renders the socialmedia headers for a root page

    :param request: The request that has been sent to the django server
    :param language: The language of the page
    :param path: The path to the page
    :return: HTML social meta headers required by social media platforms
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
    Generally renders the social media headers for a root region page.
    This is also used as a fallback for any routes in a region, where no content can be found.

    :param request: The request that has been sent to the Django Server
    :param region: The region the request refers to
    :param path: The path to the page
    :return: HTML social meta headers required by social media platforms
    """
    title = f"{region.name} | {settings.BRANDING_TITLE}"
    url = f"{settings.WEBAPP_URL}/{path}"
    return render_socialmedia_headers(request, title, None, url)


def content_socialmedia_headers(
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

    path_elements = path.split("/", maxsplit=1)
    route = path_elements[0] if len(path_elements) > 0 else None
    slug = path_elements[1] if len(path_elements) == 2 else None

    if route == "events" and slug:
        return event_socialmedia_headers(request, region, language, slug)
    if route == "locations" and slug:
        return location_socialmedia_headers(request, region, language, slug)
    if route == "news" and slug:
        # slug == /local/slug | /tunews/slug
        return news_socialmedia_headers(request, region, language, path=slug)
    return page_socialmedia_headers(request, region, language, path)


def _get_excerpt(content: str) -> str:
    return unescape(strip_tags(content))[:100]


def _get_region_title(region: Region, page_title: str) -> str:
    return f"{page_title} - {region.name} | {settings.BRANDING_TITLE}"


def event_socialmedia_headers(
    request: HttpRequest, region: Region, language: Language, slug: str
) -> Optional[HttpResponse]:
    """
    Tries rendering the socialmedia headers for an event page in a specified region and language.

    :param request: The request sent to the Django server
    :param region: The region the event is supposed to belong to
    :param language: The language the event is supposed to belong to
    :param slug: The event slug
    :return: HTML social meta headers required by social media platforms if the event page exists
    """
    if not (
        event_translation := EventTranslation.search(
            region, language.slug, slug
        ).first()
    ):
        return None

    # TODO: add event json-ld
    activate(language.slug)
    return render_socialmedia_headers(
        request=request,
        title=_get_region_title(region, event_translation.title),
        excerpt=_get_excerpt(event_translation.content),
        url=event_translation.full_url,
    )


def news_socialmedia_headers(
    request: HttpRequest, region: Region, language: Language, path: str
) -> Optional[HttpResponse]:
    """
    Tries rendering the socialmedia headers for a news page in a specified region and language.

    :param request: The request sent to the Django server
    :param region: The region the push notification is supposed to belong to
    :param language: The language the push notification is supposed to belong to
    :param path: The subpath of the news route starting with the news channel e.g. /local/1
    :return: HTML social meta headers required by social media platforms if the news page exists
    """
    path_elements = path.split("/", maxsplit=1)

    if not (slug := path_elements[1] if len(path_elements) == 2 else None):
        return None

    pn_translation = PushNotificationTranslation.objects.filter(
        language__slug=language.slug,
        push_notification=slug,
        push_notification__regions=region,
    ).first()

    if not pn_translation:
        return None

    activate(language.slug)
    return render_socialmedia_headers(
        request=request,
        title=_get_region_title(region, pn_translation.get_title()),
        excerpt=_get_excerpt(pn_translation.get_text()),
        url=f"{settings.WEBAPP_URL}/{pn_translation.get_absolute_url()}",
    )


def location_socialmedia_headers(
    request: HttpRequest, region: Region, language: Language, slug: str
) -> Optional[HttpResponse]:
    """
    Tries rendering the socialmedia headers for a location page in a specified region and language.

    :param request: The request sent to the Django server
    :param region: The region the location is supposed to belong to
    :param language: The language the location is supposed to belong to
    :param slug: The location slug
    :return: HTML social meta headers required by social media platforms if the location page exists
    """
    if not (
        location_translation := POITranslation.search(
            region, language.slug, slug
        ).first()
    ):
        return None

    activate(language.slug)
    return render_socialmedia_headers(
        request=request,
        title=_get_region_title(region, location_translation.title),
        excerpt=_get_excerpt(location_translation.content),
        url=location_translation.full_url,
    )


def page_socialmedia_headers(
    request: HttpRequest, region: Region, language: Language, path: str
) -> Optional[HttpResponse]:
    """
    Tries rendering the socialmedia headers for a page in a specified region and language.

    :param request: The request sent to the Django server
    :param region: The region the page is supposed to belong to
    :param language: The language the page is supposed to belong to
    :param path: The page path (url_infix + slug)
    :return: HTML social meta headers required by social media platforms if the page exists
    """
    if not (
        page_translation := PageTranslation.search(region, language.slug, path).first()
    ):
        return None

    # TODO: add breadcrumb json-ld if content_translation exists
    activate(language.slug)
    return render_socialmedia_headers(
        request=request,
        title=_get_region_title(region, page_translation.title),
        excerpt=_get_excerpt(page_translation.content),
        url=page_translation.full_url,
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
    :return: HTML social meta headers required by social media platforms
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
