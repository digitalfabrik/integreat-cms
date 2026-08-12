"""
This module contains views of the social media headers API endpoint.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING
from urllib.parse import unquote

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from ...cms.constants import region_status
from ...cms.models.languages.language import Language
from ...cms.utils.internal_link_utils import (
    get_public_translation_for_webapp_link_parts,
)
from ...cms.utils.social_media_utils import (
    get_excerpt,
    get_region_title,
    render_social_media_headers,
)
from ...news_managers import registry

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.http import (
        HttpRequest,
        HttpResponse,
        HttpResponseRedirect,
        JsonResponse,
    )

    from ...cms.models import Region

logger = logging.getLogger(__name__)


def get_non_archived_region(request: HttpRequest) -> Region:
    """
    Returns the region of the current request and ensures it is not archived.

    :param request: The current request

    :raises ~django.http.Http404: If the region is archived

    :return: The non-archived region of the request
    """
    region = request.region
    if region.status == region_status.ARCHIVED:
        raise Http404("This region is archived.")
    return region


def site_url(request: HttpRequest) -> str:
    """
    Extracts the path from the request and constructs the original url.

    :param request: The current request

    :return: The url for the page which the social media headers have been requested for
    """
    path = request.path
    path = path.replace("/api/v3/social", "")
    return f"{settings.WEBAPP_URL}{path}"


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


def partial_html_response(
    function: Callable,
    error_renderer: Callable = render_error_headers,
) -> Callable:
    """
    This decorator can be used to catch :class:`~django.http.Http404` exceptions and convert them to a partial HTML responses
    needed for the webapp's server side includes.

    :param function: The view function which should always return a partial HTML response
    :param error_renderer: The function which renders the partial HTML response for the error case

    :return: The decorated function
    """

    @wraps(function)
    def wrap(
        request: dict[str, str] | HttpRequest,
        *args: Any,
        **kwargs: Any,
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
            return error_renderer(
                request=request,
                error=str(e),
            )

    return wrap


@partial_html_response
def root_social_media_headers(
    request: HttpRequest,
    language_slug: str | None = None,
) -> HttpResponse:
    """
    Renders the social media headers for a root page

    :param request: The current request
    :param language_slug: The language slug of the page or the default language

    :return: HTML social meta headers required by social media platforms
    """
    language = get_object_or_404(
        Language,
        slug=language_slug or settings.LANGUAGE_CODE,
    )
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
def region_social_media_headers(
    request: HttpRequest,
    region_slug: str,
    language_slug: str | None = None,
) -> HttpResponse:
    """
    Generally renders the social media headers for a root region page.
    This is also used as a fallback for any routes in a region, where no content can be found.

    :param request: The current request
    :param language_slug: The current language

    :return: HTML social meta headers required by social media platforms
    """
    region = get_non_archived_region(request)
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
def page_social_media_headers(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    path: str,
) -> HttpResponse:
    """
    Tries rendering the social media headers for a page in a specified region and language.

    :param request: The current request
    :param language_slug: The language slug of the language, which the page belongs to
    :param path: The page path (url_infix + slug)

    :return: HTML social meta headers required by social media platforms if the page exists
    """
    region = get_non_archived_region(request)
    language = region.get_language_or_404(language_slug, only_active=True)

    path_parts = unquote(path).strip("/").split("/")
    if not (
        page_translation := get_public_translation_for_webapp_link_parts(
            region.slug,
            language_slug,
            path_parts,
        )
    ):
        raise Http404("Page not found in this region with this language.")

    # The imprint is the only content object which cannot be archived
    if getattr(page_translation.foreign_object, "archived", False):
        raise Http404("This page is archived.")

    # TODO(sarahsporck): add breadcrumb json-ld if content_translation exists
    # https://github.com/digitalfabrik/integreat-cms/issues/3287
    return render_social_media_headers(
        request=request,
        title=get_region_title(region, page_translation.title),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(page_translation.content_for_delivery()),
        url=page_translation.full_url,
    )


@partial_html_response
def event_social_media_headers(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    slug: str,
) -> HttpResponse:
    """
    Tries rendering the social_media headers for an event page in a specified region and language.

    :param request: The current request
    :param language_slug: The language slug of the language, which the event belongs to
    :param slug: The event slug

    :return: HTML social meta headers required by social media platforms if the event page exists
    """
    region = get_non_archived_region(request)
    language = region.get_language_or_404(language_slug, only_active=True)

    if not (
        event_translation := get_public_translation_for_webapp_link_parts(
            region.slug,
            language_slug,
            ["events", slug],
        )
    ):
        raise Http404("Event not found in this region with this language.")

    if event_translation.foreign_object.archived:
        raise Http404("This event is archived.")

    # TODO(sarahsporck): add event json-ld
    # https://github.com/digitalfabrik/integreat-cms/issues/3287
    return render_social_media_headers(
        request=request,
        title=get_region_title(region, event_translation.title),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(event_translation.content_for_delivery()),
        url=event_translation.full_url,
    )


@partial_html_response
def news_social_media_headers(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    news_type: str,
    news_raw_id: str,
) -> HttpResponse:
    """
    Tries rendering the social media headers for a news page in a specified region and language.

    :param request: The current request
    :param language_slug: The language slug of the language, which the news item belongs to
    :param slug: The news-source-specific identifier of the news item (e.g. /news/<news_type>/<slug>/)
    :param news_type: The :attr:`~integreat_cms.news_managers.abstract_news_manager.AbstractNewsManager.short_name` of the news source the slug refers to (e.g. ``"local"``, ``"tunews"``, ``"amalnews"``)

    :return: HTML social meta headers required by social media platforms if the news page exists
    """
    region = get_non_archived_region(request)
    language = region.get_language_or_404(language_slug, only_active=True)

    news_manager = next(
        (manager for manager in registry.CHOICES if manager.short_name == news_type),
        None,
    )

    if not news_manager:
        raise Http404("Invalid news type is given.")

    return news_manager.social_media_headers(request, region, language, news_raw_id)


@partial_html_response
def location_social_media_headers(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    slug: str,
) -> HttpResponse:
    """
    Tries rendering the social media headers for a location page in a specified region and language.

    :param request: The current request
    :param language_slug: The language slug of the language, which the location belongs to
    :param slug: The location slug

    :return: HTML social meta headers required by social media platforms if the location page exists
    """
    region = get_non_archived_region(request)
    language = region.get_language_or_404(language_slug, only_active=True)

    if not (
        location_translation := get_public_translation_for_webapp_link_parts(
            region.slug,
            language_slug,
            ["locations", slug],
        )
    ):
        raise Http404("POI not found in this region with this language.")

    if location_translation.foreign_object.archived:
        raise Http404("This location is archived.")

    return render_social_media_headers(
        request=request,
        title=get_region_title(region, location_translation.title),
        language_code=language.bcp47_tag,
        excerpt=get_excerpt(location_translation.content_for_delivery()),
        url=location_translation.full_url,
    )
