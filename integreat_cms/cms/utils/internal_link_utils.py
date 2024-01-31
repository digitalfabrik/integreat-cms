"""
This file contains utility functions for recognizing and modifying internal links
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

from django.conf import settings

from ..models import (
    Event,
    ImprintPage,
    ImprintPageTranslation,
    Page,
    PageTranslation,
    POI,
)

if TYPE_CHECKING:
    from typing import Optional

    from lxml.html import Element

    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


# pylint: disable=compare-to-zero
def update_link(
    link: Element, target_language_slug: str
) -> Optional[tuple[str, Element | str]]:
    """
    Fixes the internal link, if it is broken.
    This includes:

    - Changing the link language to `target_language_slug`
    - Fixing the link path if any part of it points to an outdated version of a content translation

    Returns a tuple of the translated url and (potentially) modified title.
    For example, with current_link = 'https://integreat.app/augsburg/de/willkommen/' and language_slug = 'en'
    a possible return value could be ('https://integreat.app/augsburg/en/welcome/, 'Welcome').
    Note that the resulting link might refer to a fallback language and not the actual target language.

    :param link: The link to be updated
    :param target_language_slug: The language slug for the target translation
    :returns: a tuple of (url, innerHtml) of the target translation, or None
    """
    if not (current_url := link.get("href")):
        return None

    if not (source_translation := get_public_translation_for_link(current_url)):
        return None

    if target_translation := source_translation.foreign_object.get_public_translation(
        target_language_slug
    ):
        # Always use the full url, even if the url was previously a short url
        fixed_link = target_translation.full_url

        # Update the title if it was previously the url, otherwise use the new title
        link_html = None
        if len(link) == 0 and link.text and current_url.strip() == link.text.strip():
            link_html = fixed_link
        elif link.get("data-integreat-auto-update") == "true":
            link_html = target_translation.link_title

        return fixed_link, link_html

    return None


WEBAPP_NETLOC: str = urlparse(settings.WEBAPP_URL).netloc
SHORT_LINKS_NETLOC: str = urlparse(settings.SHORT_LINKS_URL).netloc


def get_public_translation_for_link(url: str) -> AbstractContentTranslation | None:
    """
    This function gets the public content translation object corresponding to the path of an internal url.
    If the url does not refer to any object, this function will return None.
    This function handles webapp links and short urls.
    If the language of the url is the same as `current_language_slug`, this function will return None.

    :param url: The url
    :returns: The latest corresponding content translation
    """
    parsed_url = urlparse(url)
    if parsed_url.netloc == WEBAPP_NETLOC:
        return get_public_translation_for_webapp_link(parsed_url.path)
    if parsed_url.netloc == SHORT_LINKS_NETLOC:
        return get_public_translation_for_short_link(parsed_url.path)
    return None


def get_public_translation_for_webapp_link(
    path: str,
) -> AbstractContentTranslation | None:
    """
    Calculates the content object that corresponds to the webapp url path and returns its latest public translation.

    :param path: The url path, for example given the url 'https://integreat.app/augsburg/de/willkommen/' it would be '/augsburg/de/willkommen/'
    :returns: The latest corresponding content translation
    """
    parts: list[str] = unquote(path).strip("/").split("/")
    if len(parts) < 3:
        # Not a relevant internal url
        return None

    region_slug, language_slug, *path_parts = parts
    path = path_parts[0]
    object_slug = path_parts[-1]

    object_type = {"events": Event, "locations": POI, "disclaimer": ImprintPage}.get(
        path, Page
    )
    filter_args = {
        "region__slug": region_slug,
        "translations__language__slug": language_slug,
    }
    if object_type != ImprintPage:
        filter_args["translations__slug"] = object_slug

    if not (instances := object_type.objects.filter(**filter_args).distinct()):
        # Not a correct url to one of the supported object types
        return None

    if len(instances) > 1:
        logger.warning(
            "Violated uniqueness constraint for %s, %s, %s",
            region_slug,
            language_slug,
            object_slug,
        )

    instance = instances[0]
    return instance.get_public_translation(language_slug)


def get_public_translation_for_short_link(
    path: str,
) -> AbstractContentTranslation | None:
    """
    Calculates the content object that corresponds to the short url path and returns its latest public translation.

    :param path: The url path, for example given the url 'http://localhost:8000/s/p/124/' it would be '/s/p/124/'
    :returns: The latest corresponding content translation
    """
    parts: list[str] = unquote(path).strip("/").split("/")
    if len(parts) != 3 or parts[0] != "s":
        # Not a relevant internal url
        return None

    if parts[1] == "p":
        object_type = PageTranslation
    elif parts[1] == "i":
        object_type = ImprintPageTranslation
    else:
        return None

    try:
        object_id = int(parts[2])
    except ValueError:
        return None

    if not (instance := object_type.objects.get(id=object_id)):
        return None

    return instance.public_version
