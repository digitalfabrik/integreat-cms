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

from integreat_cms.cms.models.events.event_translation import EventTranslation
from integreat_cms.cms.models.languages.language import Language
from integreat_cms.cms.models.pois.poi_translation import POITranslation
from integreat_cms.cms.models.push_notifications.push_notification_translation import (
    PushNotificationTranslation,
)
from integreat_cms.cms.models.regions.region import Region

from ...cms.models import PageTranslation

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


def site_url(request: HttpRequest) -> str:
    """
    Extracts the path from the request and constructs the original url.

    :param request: The request that has been sent to the django server
    :return: The url for the page which the social media headers have been requested for
    """
    path = request.path
    path = path.replace("/api/v3/social", "")
    return f"{settings.WEBAPP_URL}{path}"


def root_social_media_headers(
    request: HttpRequest, language_slug: str = settings.LANGUAGE_CODE
) -> HttpResponse:
    """
    Renders the social media headers for a root page

    :param request: The request that has been sent to the django server
    :param language_slug: The language slug of the page or the default language
    :return: HTML social meta headers required by social media platforms
    """
    language = Language.objects.get(slug=language_slug)
    title = language.social_media_webapp_title or settings.BRANDING_TITLE
    url = site_url(request)

    return render_social_media_headers(
        request,
        title,
        language.bcp47_tag,
        language.social_media_webapp_description,
        url,
    )


# pylint: disable=unused-argument
def region_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str = settings.LANGUAGE_CODE
) -> HttpResponse:
    """
    Generally renders the social media headers for a root region page.
    This is also used as a fallback for any routes in a region, where no content can be found.

    :param request: The request that has been sent to the Django Server
    :param social_region_slug: The region the request refers to
    :param language_slug: The current language
    :param path: The path to the page
    :return: HTML social meta headers required by social media platforms
    """
    region = request.region
    language = region.get_language_or_404(language_slug)

    title = f"{region.name} | {settings.BRANDING_TITLE}"
    url = site_url(request)
    return render_social_media_headers(request, title, language.bcp47_tag, None, url)


def get_excerpt(content: str) -> str:
    """
    Correctly escapes, truncates and normalizes the content of the page to display in a search result

    :param content: The content of the page
    :return: A page excerpt containing the first 100 characters of "raw" content
    """
    return unescape(strip_tags(content))[:100]


def get_region_title(region: Region, page_title: str) -> str:
    """
    Constructs in a unified format the page title of a page in a region.

    :param region: The region where the page resides in
    :param page_title: The title of the page
    :return: The constructed page title
    """
    return f"{page_title} - {region.name} | {settings.BRANDING_TITLE}"


# pylint: disable=unused-argument
def event_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str, slug: str
) -> HttpResponse:
    """
    Tries rendering the social_media headers for an event page in a specified region and language.

    :param request: The request sent to the Django server
    :param region_slug: The region slug for the region, which the event belongs to
    :param language_slug: The language slug of the language, which the event belongs to
    :param slug: The event slug
    :return: HTML social meta headers required by social media platforms if the event page exists
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    if not (
        event_translation := EventTranslation.search(
            region, language.slug, slug
        ).first()
    ):
        raise Http404("Event not found in this region with this language.")

    # TODO: add event json-ld
    return render_social_media_headers(
        request=request,
        title=get_region_title(region, event_translation.title),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(event_translation.content),
        url=event_translation.full_url,
    )


# pylint: disable=unused-argument
def news_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str, slug: str
) -> HttpResponse:
    """
    Tries rendering the social media headers for a news page in a specified region and language.

    :param request: The request sent to the Django server
    :param region_slug: The region slug for the region, which the push notification belongs to
    :param language_slug: The language slug of the language, which the push notification belongs to
    :param slug: The news specific slug of the news route e.g. /local/<slug>
    :return: HTML social meta headers required by social media platforms if the news page exists
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    pn_translation = PushNotificationTranslation.objects.filter(
        language__slug=language.slug,
        push_notification__id=slug,
        push_notification__regions=region,
    ).first()

    if not pn_translation:
        raise Http404("Push Notification not found in this region with this language.")

    return render_social_media_headers(
        request=request,
        title=get_region_title(region, pn_translation.get_title()),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(pn_translation.get_text()),
        url=f"{settings.WEBAPP_URL}{pn_translation.get_absolute_url()}",
    )


# pylint: disable=unused-argument
def location_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str, slug: str
) -> HttpResponse:
    """
    Tries rendering the social media headers for a location page in a specified region and language.

    :param request: The request sent to the Django server
    :param region_slug: The region slug for the region, which the location belongs to
    :param language_slug: The language slug of the language, which the location belongs to
    :param slug: The location slug
    :return: HTML social meta headers required by social media platforms if the location page exists
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    if not (
        location_translation := POITranslation.search(
            region, language.slug, slug
        ).first()
    ):
        raise Http404("POI not found in this region with this language.")

    return render_social_media_headers(
        request=request,
        title=get_region_title(region, location_translation.title),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(location_translation.content),
        url=location_translation.full_url,
    )


# pylint: disable=unused-argument
def page_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str, path: str
) -> HttpResponse:
    """
    Tries rendering the social media headers for a page in a specified region and language.

    :param request: The request sent to the Django server
    :param region_slug: The region slug for the region, which the page belongs to
    :param language_slug: The language slug of the language, which the page belongs to
    :param path: The page path (url_infix + slug)
    :return: HTML social meta headers required by social media platforms if the page exists
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    if not (
        page_translation := PageTranslation.search(region, language.slug, path).first()
    ):
        raise Http404("Page not found in this region with this language.")

    # TODO: add breadcrumb json-ld if content_translation exists
    return render_social_media_headers(
        request=request,
        title=get_region_title(region, page_translation.title),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(page_translation.content),
        url=page_translation.full_url,
    )


def render_social_media_headers(
    request: HttpRequest, title: str, language_code: str, excerpt: str | None, url: str
) -> HttpResponse:
    """
    Renders the social media headers with the specified arguments

    :param request: The request sent to the Django Server
    :param title: The title of the page in the social media headers
    :param language_code: The language of the page
    :param excerpt: An optional excerpt describing the content of the page. If omitted google, will automatically crawl an excerpt
    :param url: The url the headers belong to
    :return: HTML social meta headers required by social media platforms
    """
    return render(
        request,
        "social_media_headers.html",
        {
            "title": title,
            "excerpt": excerpt,
            "platform": settings.BRANDING_TITLE,
            "url": url,
            "image": f"{settings.BASE_URL}/{settings.SOCIAL_PREVIEW_IMAGE}",
            "language_code": language_code,
        },
    )
