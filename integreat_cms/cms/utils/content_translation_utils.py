"""
This file contains utility functions for content translations.
"""
from __future__ import annotations

import logging
from copy import deepcopy
from html import unescape
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.db.models import Q
from linkcheck.models import Url
from lxml.etree import LxmlError
from lxml.html import fromstring, tostring

from ..models import MediaFile
from ..utils import internal_link_utils
from .internal_link_utils import get_public_translation_for_link
from .linkcheck_utils import save_new_version

if TYPE_CHECKING:
    from ..models import User
    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


# pylint: disable=too-many-branches, too-many-locals
def get_cleaned_content(content_str: str, language_slug: str) -> str:
    """
    Validate the content and applies changes
        to ``<img>``- and ``<a>``-Tags to match the guidelines.

    :param content_str: The content to clean
    :param language_slug: The language slug of the content
    :return: The cleaned content
    """
    try:
        content = fromstring(content_str)
    except LxmlError:
        # The content is not guaranteed to be valid html, for example it may be empty
        return content_str

    # Convert heading 1 to heading 2
    for heading in content.iter("h1"):
        heading.tag = "h2"
        logger.debug("Replaced heading 1 with heading 2: %r", tostring(heading))

    # Convert pre and code tags to p tags
    for monospaced in content.iter("pre", "code"):
        tag_type = monospaced.tag
        monospaced.tag = "p"
        logger.debug("Replaced %r tag with p tag: %r", tag_type, tostring(monospaced))

    # Remove external links
    for link in content.iter("a"):
        link.attrib.pop("target", None)
        logger.debug("Removed target attribute from link: %r", tostring(link))

    # Set link-external as class for external links
    for link in content.iter("a"):
        if href := link.get("href"):
            is_external = not any(url in href for url in settings.INTERNAL_URLS)
            if "link-external" not in link.classes and is_external:
                link.classes.add("link-external")
                logger.debug("Added class 'link-external' to %r", tostring(link))
            elif "link-external" in link.classes and not is_external:
                link.classes.remove("link-external")
                logger.debug("Removed class 'link-external' from %r", tostring(link))

    # Update internal links
    for link in content.iter("a"):
        if translation := internal_link_utils.update_link(link, language_slug):
            new_url, new_html = translation
            if new_url != unquote(link.get("href", "")):
                link.set("href", new_url)
                logger.debug(
                    "Updated link url from %s to %s", link.get("href"), new_url
                )

            if new_html is not None:
                logger.debug("Updated link text from %s to %s", link.text, new_html)
                for child in link:
                    link.remove(child)
                if isinstance(new_html, str):
                    link.text = unescape(new_html)
                else:
                    link.text = ""
                    link.append(new_html)

    # Scan for media files in content and replace alt texts
    for image in content.iter("img"):
        logger.debug("Image tag found in content (src: %s)", image.attrib["src"])
        # Remove host
        relative_url = urlparse(image.attrib["src"]).path
        # Remove media url prefix if exists
        if relative_url.startswith(settings.MEDIA_URL):
            relative_url = relative_url[len(settings.MEDIA_URL) :]
        # Check whether media file exists in database
        media_file = MediaFile.objects.filter(
            Q(file=relative_url) | Q(thumbnail=relative_url)
        ).first()
        # Replace alternative text
        if media_file and media_file.alt_text:
            logger.debug("Image alt text replaced: %r", media_file.alt_text)
            image.attrib["alt"] = media_file.alt_text

    return tostring(content, with_tail=False).decode("utf-8")


def update_links_to(
    content_translation: AbstractContentTranslation, user: User | None
) -> None:
    """
    Updates all content translations with links that point to the given translation.
    This fixes potentially outdated links.

    :param content_translation: The content translation for which links that points to it should get updated
    :param user: The user who should be responsible for updating the links
    """
    for outdated_content_translation in get_referencing_translations(
        content_translation
    ):
        # Assert that the related translation is not archived
        # Note that this should not be possible, since links to archived pages get deleted
        if getattr(outdated_content_translation.foreign_object, "archived", False):
            continue

        new_content = get_cleaned_content(
            outdated_content_translation.content,
            outdated_content_translation.language.slug,
        )
        if new_content == outdated_content_translation.content:
            continue

        fixed_content_translation = deepcopy(outdated_content_translation)
        fixed_content_translation.content = new_content
        save_new_version(outdated_content_translation, fixed_content_translation, user)

        logger.debug(
            "Updated links to %s in %r",
            content_translation.full_url,
            outdated_content_translation,
        )


def get_referencing_translations(
    content_translation: AbstractContentTranslation,
) -> set[AbstractContentTranslation]:
    """
    Returns a list of content translations that link to the given translation

    :param content_translation: The `content_translation` for which links should be searched
    :return: All referencing content translations
    """
    result = set()

    public_translation = content_translation.public_version

    urls = (url for url in Url.objects.all() if url.internal)
    for url in urls:
        if linked_translation := get_public_translation_for_link(url.url):
            if linked_translation != public_translation:
                continue

            for link in url.links.all():
                result.add(link.content_object.latest_version)
    return result
