"""
This file contains utility functions for recognizing and modifying internal links
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

from django.conf import settings

from ..constants import status
from ..models import (
    EventTranslation,
    ImprintPageTranslation,
    PageTranslation,
    POITranslation,
)

if TYPE_CHECKING:
    from lxml.html import Element

    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


def update_link(
    link: Element,
    target_language_slug: str,
) -> tuple[str, Element | str] | None:
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

    try:
        target_translation = source_translation.foreign_object.get_public_translation(
            target_language_slug
        )
    except KeyError:
        logger.exception(
            "Could not resolve link translation due to missing language %s.",
            target_language_slug,
        )
        return source_translation.full_url, source_translation.link_title
    if target_translation:
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

    return get_public_translation_for_webapp_link_parts(
        region_slug,
        language_slug,
        path_parts,
    )


def get_public_translation_for_webapp_link_parts(
    region_slug: str,
    language_slug: str,
    path_parts: list[str],
) -> AbstractContentTranslation | None:
    """
    Calculates the content translation that corresponds to the given path, region slug and language slug.

    :param region_slug: The slug of the region of the translation
    :param language_slug: The slug of the language of the translation
    :param path_parts: A list of the path parts of the translations url. For example ['events', 'test-event']
    """
    path = path_parts[0]
    object_slug = path_parts[-1]

    object_type, foreign_object = {
        "events": (EventTranslation, "event"),
        "locations": (POITranslation, "poi"),
        "disclaimer": (ImprintPageTranslation, "page"),
    }.get(path, (PageTranslation, "page"))
    filter_args = {
        f"{foreign_object}__region__slug": region_slug,
        "language__slug": language_slug,
        "status": status.PUBLIC,
    }
    if object_type != ImprintPageTranslation:
        filter_args[f"{foreign_object}__translations__slug"] = object_slug

    instances = (
        object_type.objects.filter(**filter_args)
        .select_related("language", f"{foreign_object}__region")
        .order_by("-version")
    )

    return instances.first()


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
