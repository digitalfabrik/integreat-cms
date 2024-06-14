"""
This file contains utility functions for content translations.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from django.conf import settings
from django.db.models import Q
from lxml.etree import LxmlError
from lxml.html import fromstring, tostring

from ..models import MediaFile
from ..utils import internal_link_utils
from ..utils.linkcheck_utils import fix_content_link_encoding

logger = logging.getLogger(__name__)


def get_cleaned_content(content_str: str, language_slug: str) -> str:
    """
    Validate the content and applies changes
    to ``<img>``- and ``<a>``-Tags to match the guidelines.

    :raises ~django.core.exceptions.ValidationError: When a heading 1 (``<h1>``) is used in the text content
    :param content_str: The content to clean
    :param language_slug: The language slug of the content
    :return: The valid content
    """
    try:
        content = fromstring(content_str)
    except LxmlError:
        # The content is not guaranteed to be valid html, for example it may be empty
        return content_str

    # Convert heading 1 to heading 2
    for heading in content.iter("h1"):
        heading.tag = "h2"
        logger.debug(
            "Replaced heading 1 with heading 2: %r",
            tostring(heading, encoding="unicode"),
        )

    # Convert pre and code tags to p tags
    for monospaced in content.iter("pre", "code"):
        tag_type = monospaced.tag
        monospaced.tag = "p"
        logger.debug(
            "Replaced %r tag with p tag: %r",
            tag_type,
            tostring(monospaced, encoding="unicode"),
        )

    # Set link-external as class for external links
    for link in content.iter("a"):
        if href := link.get("href"):
            is_external = not any(url in href for url in settings.INTERNAL_URLS)
            if "link-external" not in link.classes and is_external:
                link.classes.add("link-external")
                logger.debug(
                    "Added class 'link-external' to %r",
                    tostring(link, encoding="unicode"),
                )
            elif "link-external" in link.classes and not is_external:
                link.classes.remove("link-external")
                logger.debug(
                    "Removed class 'link-external' from %r",
                    tostring(link, encoding="unicode"),
                )

    # Remove external links
    for link in content.iter("a"):
        link.attrib.pop("target", None)
        logger.debug(
            "Removed target attribute from link: %r",
            tostring(link, encoding="unicode"),
        )

    # Update internal links
    for link in content.iter("a"):
        if href := link.attrib.get("href"):
            if translation := internal_link_utils.update_link_language(
                href, link.text, language_slug
            ):
                translated_url, translated_text = translation
                link.set("href", translated_url)
                # translated_text might be None if the link tag consists of other tags instead of plain text
                if translated_text:
                    link.text = translated_text
                logger.debug("Updated link url from %s to %s", href, translated_url)

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

    content_str = tostring(content, encoding="unicode", with_tail=False)
    return fix_content_link_encoding(content_str)
