"""
This module contains views of the raw content API endpoint for LLM agents.
"""

from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING
from urllib.parse import unquote

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from ...cms.models.languages.language import Language
from ...cms.utils.internal_link_utils import (
    get_public_translation_for_webapp_link_parts,
)
from ...cms.utils.social_media_utils import (
    get_region_title,
)
from ...news_managers import registry
from .social_media_headers import (
    get_non_archived_region,
    partial_html_response,
)

if TYPE_CHECKING:
    from django.http import (
        HttpRequest,
        HttpResponse,
    )

    from ...cms.models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


def render_error_content(request: HttpRequest, error: str) -> HttpResponse:
    """
    Renders the partial HTML response for the webapp's server side include.

    In contrast to :func:`~integreat_cms.api.v3.social_media_headers.render_error_headers`, this is included in the
    body of the webapp's document, so it must not contain any ``<html>`` or ``<head>`` elements.

    :param request: The current request
    :param error: The error message

    :return: Partial HTML response for the webapp's server side include
    """
    return render(
        request,
        "raw_content_error.html",
        {
            "error": error,
        },
        status=404,
    )


#: Variant of :func:`~integreat_cms.api.v3.social_media_headers.partial_html_response` which renders errors as a
#: partial HTML body instead of partial HTML headers
partial_content_response = partial(
    partial_html_response,
    error_renderer=render_error_content,
)


def get_content(
    request: HttpRequest,
    translation: AbstractContentTranslation,
) -> str:
    """
    Returns the content of a translation with all shortcodes expanded

    :param request: The current request
    :param translation: The translation whose content should be rendered

    :return: The content of the translation
    """
    return translation.content_for_delivery(request=request)


@partial_content_response
def root_content(
    request: HttpRequest,
    language_slug: str = settings.LANGUAGE_CODE,
) -> HttpResponse:
    """
    Renders the raw HTML content for a root page

    :param request: The current request
    :param language_slug: The language slug of the page or the default language

    :return: Raw HTML content of the root page
    """
    language = get_object_or_404(Language, slug=language_slug)
    title = language.social_media_webapp_title or settings.BRANDING_TITLE

    return render(
        request,
        "raw_content.html",
        {
            "title": title,
            "content": "",
            "language_code": language.bcp47_tag,
        },
    )


@partial_content_response
def region_content(
    request: HttpRequest,
    region_slug: str,
    language_slug: str | None = None,
) -> HttpResponse:
    """
    Generally renders the raw HTML content for a root region page.
    This is also used as a fallback for any routes in a region, where no content can be found.

    :param request: The current request
    :param language_slug: The current language

    :return: Raw HTML content of the region page
    """
    region = get_non_archived_region(request)
    if language_slug:
        language = region.get_language_or_404(language_slug, only_active=True)
    elif region.default_language:
        language = region.default_language
    else:
        raise Http404("Region has no default language.")

    title = f"{region.name} | {settings.BRANDING_TITLE}"

    return render(
        request,
        "raw_content.html",
        {
            "title": title,
            "content": "",
            "language_code": language.bcp47_tag,
        },
    )


@partial_content_response
def page_content(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    path: str,
) -> HttpResponse:
    """
    Tries rendering the raw HTML content for a page in a specified region and language.

    :param request: The current request
    :param language_slug: The language slug of the language, which the page belongs to
    :param path: The page path (url_infix + slug)

    :return: Raw HTML content of the page if it exists
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

    return render(
        request,
        "raw_content.html",
        {
            "title": get_region_title(region, page_translation.title),
            "content": get_content(request, page_translation),
            "language_code": language.bcp47_tag,
        },
    )


@partial_content_response
def event_content(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    slug: str,
) -> HttpResponse:
    """
    Tries rendering the raw HTML content for an event page in a specified region and language.

    :param request: The current request
    :param language_slug: The language slug of the language, which the event belongs to
    :param slug: The event slug

    :return: Raw HTML content of the event page if it exists
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

    return render(
        request,
        "raw_content.html",
        {
            "title": get_region_title(region, event_translation.title),
            "content": get_content(request, event_translation),
            "language_code": language.bcp47_tag,
        },
    )


@partial_content_response
def news_content(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    news_type: str,
    news_raw_id: str,
) -> HttpResponse:
    """
    Tries rendering the raw HTML content for a news page in a specified region and language.

    :param request: The current request
    :param language_slug: The language slug of the language, which the news item belongs to
    :param news_type: The short_name of the news source (e.g. "local", "tunews", "amalnews")
    :param news_raw_id: The news-source-specific identifier

    :return: Raw HTML content of the news page if it exists
    """
    region = get_non_archived_region(request)
    language = region.get_language_or_404(language_slug, only_active=True)

    news_manager = next(
        (manager for manager in registry.CHOICES if manager.short_name == news_type),
        None,
    )

    if not news_manager:
        raise Http404("Invalid news type is given.")

    return news_manager.raw_content(request, region, language, news_raw_id)


@partial_content_response
def location_content(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    slug: str,
) -> HttpResponse:
    """
    Tries rendering the raw HTML content for a location page in a specified region and language.

    :param request: The current request
    :param language_slug: The language slug of the language, which the location belongs to
    :param slug: The location slug

    :return: Raw HTML content of the location page if it exists
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

    return render(
        request,
        "raw_content.html",
        {
            "title": get_region_title(region, location_translation.title),
            "content": get_content(request, location_translation),
            "language_code": language.bcp47_tag,
        },
    )
