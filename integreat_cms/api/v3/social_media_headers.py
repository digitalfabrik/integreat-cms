"""
This module contains views of the social media headers API endpoint.
"""

from __future__ import annotations

import logging
from functools import wraps
from html import unescape
from typing import TYPE_CHECKING
from urllib.parse import unquote

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.html import strip_tags

from ...cms.models.languages.language import Language
from ...cms.models.push_notifications.push_notification_translation import (
    PushNotificationTranslation,
)
from ...cms.models.regions.region import Region
from ...cms.utils.internal_link_utils import (
    get_public_translation_for_webapp_link_parts,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.http import (
        HttpRequest,
        HttpResponse,
        HttpResponseRedirect,
        JsonResponse,
    )

logger = logging.getLogger(__name__)


def get_excerpt(content: str) -> str:
    """
    Correctly escapes, truncates and normalizes the content of the page to display in a search result

    :param content: The content of the page

    :return: A page excerpt containing the first 100 characters of "raw" content
    """
    return unescape(strip_tags(content))[:100].replace("\n", " ").replace("\r", "")


def get_region_title(region: Region, page_title: str) -> str:
    """
    Constructs in a unified format the page title of a page in a region.

    :param region: The region where the page resides in
    :param page_title: The title of the page

    :return: The constructed page title
    """
    return f"{page_title} - {region.name} | {settings.BRANDING_TITLE}"


def site_url(request: HttpRequest) -> str:
    """
    Extracts the path from the request and constructs the original url.

    :param request: The current request

    :return: The url for the page which the social media headers have been requested for
    """
    path = request.path
    path = path.replace("/api/v3/social", "")
    return f"{settings.WEBAPP_URL}{path}"


def partial_html_response(function: Callable) -> Callable:
    """
    This decorator can be used to catch :class:`~django.http.Http404` exceptions and convert them to a partial HTML responses
    needed for the webapp's server side includes.

    :param function: The view function which should always return a partial HTML response

    :return: The decorated function
    """

    @wraps(function)
    def wrap(
        request: dict[str, str] | HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect | JsonResponse:
        r"""
        The inner function for this decorator.
        It tries to execute the decorated view function and returns the unaltered result with the exception of a
        :class:`~django.http.Http404` error, which is converted into a partial HTML response

        :param request: Django request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied kwargs

        :return: The response of the given function or a partial :class:`~django.http.HttpResponse`
        """
        try:
            return function(request, *args, **kwargs)
        except Http404 as e:
            return render_error_headers(
                request=request,
                error=str(e),
            )

    return wrap


def render_social_media_headers(
    request: HttpRequest, title: str, language_code: str, excerpt: str | None, url: str
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
            "title": title,
            "excerpt": excerpt,
            "url": url,
            "image": f"{settings.BASE_URL}/{settings.SOCIAL_PREVIEW_IMAGE}",
            "language_code": language_code,
        },
    )


def render_error_headers(request: HttpRequest, error: str) -> HttpResponse:
    """
    Renders the partial HTML response for the webapp's server side include

    :param request: The current request
    :param error: The error message

    :return: Partial HTML response for the webapp's server side include
    """
    return render(
        request,
        "error_headers.html",
        {
            "title": f"Error 404 | {settings.BRANDING_TITLE}",
            "error": error,
        },
        status=404,
    )


@partial_html_response
def root_social_media_headers(
    request: HttpRequest, language_slug: str = settings.LANGUAGE_CODE
) -> HttpResponse:
    """
    Renders the social media headers for a root page

    :param request: The current request
    :param language_slug: The language slug of the page or the default language

    :return: HTML social meta headers required by social media platforms
    """
    language = get_object_or_404(Language, slug=language_slug)
    title = language.social_media_webapp_title or settings.BRANDING_TITLE
    url = site_url(request)

    return render_social_media_headers(
        request,
        title,
        language.bcp47_tag,
        language.social_media_webapp_description,
        url,
    )


@partial_html_response
# pylint: disable=unused-argument
def region_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str | None = None
) -> HttpResponse:
    """
    Generally renders the social media headers for a root region page.
    This is also used as a fallback for any routes in a region, where no content can be found.

    :param request: The current request
    :param region_slug: The region the request refers to
    :param language_slug: The current language

    :return: HTML social meta headers required by social media platforms
    """
    region = request.region
    if language_slug:
        language = region.get_language_or_404(language_slug, only_active=True)
    elif region.default_language:
        language = region.default_language
    else:
        raise Http404("Region has no default language.")

    title = f"{region.name} | {settings.BRANDING_TITLE}"
    url = site_url(request)
    return render_social_media_headers(request, title, language.bcp47_tag, None, url)


@partial_html_response
# pylint: disable=unused-argument, fixme
def page_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str, path: str
) -> HttpResponse:
    """
    Tries rendering the social media headers for a page in a specified region and language.

    :param request: The current request
    :param region_slug: The region slug for the region, which the page belongs to
    :param language_slug: The language slug of the language, which the page belongs to
    :param path: The page path (url_infix + slug)

    :return: HTML social meta headers required by social media platforms if the page exists
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    path_parts = unquote(path).strip("/").split("/")
    if not (
        page_translation := get_public_translation_for_webapp_link_parts(
            region.slug, language_slug, path_parts
        )
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


@partial_html_response
# pylint: disable=unused-argument, fixme
def event_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str, slug: str
) -> HttpResponse:
    """
    Tries rendering the social_media headers for an event page in a specified region and language.

    :param request: The current request
    :param region_slug: The region slug for the region, which the event belongs to
    :param language_slug: The language slug of the language, which the event belongs to
    :param slug: The event slug

    :return: HTML social meta headers required by social media platforms if the event page exists
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    if not (
        event_translation := get_public_translation_for_webapp_link_parts(
            region.slug, language_slug, ["events", slug]
        )
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


@partial_html_response
# pylint: disable=unused-argument
def news_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str, slug: str
) -> HttpResponse:
    """
    Tries rendering the social media headers for a news page in a specified region and language.

    :param request: The current request
    :param region_slug: The region slug for the region, which the push notification belongs to
    :param language_slug: The language slug of the language, which the push notification belongs to
    :param slug: The news specific slug of the news route e.g. /local/<slug>

    :return: HTML social meta headers required by social media platforms if the news page exists
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    if not (
        pn_translation := PushNotificationTranslation.objects.filter(
            language__slug=language.slug,
            push_notification__id=slug,
            push_notification__regions=region,
        ).first()
    ):
        raise Http404("Push Notification not found in this region with this language.")

    return render_social_media_headers(
        request=request,
        title=get_region_title(region, pn_translation.get_title()),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(pn_translation.get_text()),
        url=f"{settings.WEBAPP_URL}{pn_translation.get_absolute_url()}",
    )


@partial_html_response
# pylint: disable=unused-argument
def location_social_media_headers(
    request: HttpRequest, region_slug: str, language_slug: str, slug: str
) -> HttpResponse:
    """
    Tries rendering the social media headers for a location page in a specified region and language.

    :param request: The current request
    :param region_slug: The region slug for the region, which the location belongs to
    :param language_slug: The language slug of the language, which the location belongs to
    :param slug: The location slug

    :return: HTML social meta headers required by social media platforms if the location page exists
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    if not (
        location_translation := get_public_translation_for_webapp_link_parts(
            region.slug, language_slug, ["locations", slug]
        )
    ):
        raise Http404("POI not found in this region with this language.")

    return render_social_media_headers(
        request=request,
        title=get_region_title(region, location_translation.title),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(location_translation.content),
        url=location_translation.full_url,
    )
