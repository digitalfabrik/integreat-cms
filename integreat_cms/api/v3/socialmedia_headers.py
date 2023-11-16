"""
This module includes functions related to the social media headers API endpoint.
"""
import logging
from html import unescape

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils.html import strip_tags
from django.utils.translation import activate

from integreat_cms.cms.models.events.event_translation import EventTranslation
from integreat_cms.cms.models.pois.poi_translation import POITranslation
from integreat_cms.cms.models.push_notifications.push_notification_translation import (
    PushNotificationTranslation,
)

from ...cms.models import PageTranslation

logger = logging.getLogger(__name__)


def root_socialmedia_headers(request, path):
    title = f"{settings.BRANDING_TITLE} | Web-App | Local Information for You"
    url = f"{settings.WEBAPP_URL}/{path}"
    if settings.BRANDING == "aschaffenburg":
        excerpt = (
            "hallo aschaffenburg is your digital companion for the town of Aschaffenburg. Here"
            " you can find local information, advice centres and services."
        )
    else:
        excerpt = (
            settings.BRANDING_TITLE + " is your digital companion for Germany. Here"
            " you can find local information, advice centres and services."
        )
    return render_socialmedia_headers(request, title, excerpt, url)


# pylint: disable=unused-argument
def region_socialmedia_headers(request, region_slug, language_slug, path=None):
    """
    Renders the social media headers for a single page

    :param request: The request that has been sent to the Django server
    :type request: ~django.http.HttpRequest

    :param region_slug: Slug defining the region
    :type region_slug: str

    :param language_slug: Code to identify the desired language
    :type language_slug: str

    :return: HTML meta headers required by social media platforms
    :rtype: ~django.template.response.TemplateResponse
    """
    region = request.region
    title = f"{region.name} | {settings.BRANDING_TITLE}"
    excerpt = ""  # TODO: individual excerpt per city
    url = f"{settings.WEBAPP_URL}/{region_slug}/{language_slug}/{path if path else ''}"
    return render_socialmedia_headers(request, title, excerpt, url)


# pylint: disable=unused-argument
def page_socialmedia_headers(request, region_slug, language_slug, path):
    """
    Renders the social media headers for a single page

    :param request: The request that has been sent to the Django server
    :type request: ~django.http.HttpRequest

    :param region_slug: Slug defining the region
    :type region_slug: str

    :param language_slug: Code to identify the desired language
    :type language_slug: str

    :param path: Should be a page translation slug
    :type path: str

    :return: HTML meta headers required by social media platforms
    :rtype: ~django.template.response.TemplateResponse
    """

    region = request.region
    route, *route_path = path.split("/", maxsplit=1)

    if route == "events" and len(route_path):
        # TODO: add event json-ld
        content_translation = EventTranslation.search(
            region, language_slug, *route_path
        ).first()
    elif route == "locations" and len(route_path):
        content_translation = POITranslation.search(
            region, language_slug, *route_path
        ).first()
    elif route == "news" and len(route_path):
        content_translation = PushNotificationTranslation.search(
            region, language_slug, *route_path
        ).first()
    else:
        # TODO: add breadcrumb json-ld if content_translation exists
        content_translation = PageTranslation.search(
            request.region, language_slug, path
        ).first()

        if not content_translation:
            # not a category route e.g. /imprint, /events
            return region_socialmedia_headers(request, region_slug, language_slug, path)

    activate(language_slug)

    if not content_translation:
        raise Http404

    excerpt = unescape(strip_tags(content_translation.content))[:100]
    title = f"{content_translation.title} | {settings.BRANDING_TITLE}"
    return render_socialmedia_headers(
        request, title, excerpt, content_translation.full_url
    )


def render_socialmedia_headers(request, title, excerpt, url):
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
