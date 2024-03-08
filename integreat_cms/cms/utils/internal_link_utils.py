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
    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


def update_link_language(
    current_link: str, link_text: str, target_language_slug: str
) -> tuple[str, str] | None:
    """
    Fixes the link, so that it points to the correct language.
    Returns a tuple of the translated url and (potentially) translated title.
    For example, with current_link = 'https://integreat.app/augsburg/de/willkommen/' and language_slug = 'en'
    a possible return value could be ('https://integreat.app/augsburg/en/welcome/, 'Welcome').
    Note that the resulting link might refer to a fallback language and not the actual target language.

    :param current_link: The link to the content translation
    :param link_text: The text of the link
    :param target_language_slug: The language slug for the target translation
    :returns: a tuple of (url, title) of the target translation, or None
    """
    source_translation = get_public_translation_for_link(
        current_link, current_language_slug=target_language_slug
    )
    if not source_translation:
        return None

    if target_translation := source_translation.foreign_object.get_public_translation(
        target_language_slug
    ):
        # Always use the full url, even if the url was previously a short url
        fixed_link = target_translation.full_url

        # Update the title if it was previously the translation title or the url
        if link_text:
            if source_translation.title.lower() == link_text.strip().lower():
                link_text = target_translation.title
            elif current_link.strip() == link_text.strip():
                link_text = fixed_link

        return fixed_link, link_text

    return None


WEBAPP_NETLOC: str = urlparse(settings.WEBAPP_URL).netloc
SHORT_LINKS_NETLOC: str = urlparse(settings.SHORT_LINKS_URL).netloc


def get_public_translation_for_link(
    url: str, current_language_slug: str | None = None
) -> AbstractContentTranslation | None:
    """
    This function gets the public content translation object corresponding to the path of an internal url.
    If the url does not refer to any object, this function will return None.
    This function handles webapp links and short urls.
    If the language of the url is the same as `current_language_slug`, this function will return None.

    :param url: The url
    :param current_language_slug: A language slug that will cause the function to return early if contained in the url
    :returns: The latest corresponding content translation
    """
    parsed_url = urlparse(url)
    if parsed_url.netloc == WEBAPP_NETLOC:
        return get_public_translation_for_webapp_link(
            parsed_url.path, current_language_slug
        )
    if parsed_url.netloc == SHORT_LINKS_NETLOC:
        return get_public_translation_for_short_link(parsed_url.path)
    return None


def get_public_translation_for_webapp_link(
    path: str, current_language_slug: str | None = None
) -> AbstractContentTranslation | None:
    """
    Calculates the content object that corresponds to the webapp url path and returns its latest public translation.

    :param path: The url path, for example given the url 'https://integreat.app/augsburg/de/willkommen/' it would be '/augsburg/de/willkommen/'
    :param current_language_slug: A language slug that will cause the function to return early if contained in the url
    :returns: The latest corresponding content translation
    """
    parts: list[str] = unquote(path).strip("/").split("/")
    if len(parts) < 3:
        # Not a relevant internal url
        return None

    region_slug, language_slug, *path_parts = parts

    if language_slug == current_language_slug:
        # Return early if the language slug is not different
        return None

    return get_public_translation_for_webapp_link_parts(
        region_slug, language_slug, path_parts
    )


def get_public_translation_for_webapp_link_parts(
    region_slug: str, language_slug: str, path_parts: list[str]
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
