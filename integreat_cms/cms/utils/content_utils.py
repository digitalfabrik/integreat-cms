import logging
from urllib.parse import urlparse

from django.conf import settings
from django.db.models import Q
from lxml.html import HtmlElement, tostring

from ..models import MediaFile
from ..utils import internal_link_utils


def clean_content(content: HtmlElement, language_slug: str) -> None:
    """
    This is the super function to clean content

    :param content: the body of content that should be cleaned
    :param language_slug: Slug of the current language
    """
    convert_heading(content)
    convert_monospaced_tags(content)
    update_links(content, language_slug)
    process_images(content)


def convert_heading(content: HtmlElement) -> None:
    """
    Converts every ``h1`` tag in the content to a ``h2`` for SEO purposes.

    :param content: the body of content of which every ``h1`` should be converted to an ``h2``.
    """
    for heading in content.iter("h1"):
        heading.tag = "h2"
        logging.debug(
            "Replaced heading 1 with heading 2: %r",
            tostring(heading, encoding="unicode"),
        )


def convert_monospaced_tags(content: HtmlElement) -> None:
    """
    Converts ``pre`` and ``code`` tags to ``p`` tags.

    :param content: the body of content of which every ``pre`` and ``code`` tag should be transformed
    """
    for monospaced in content.iter("pre", "code"):
        tag_type = monospaced.tag
        monospaced.tag = "p"
        logging.debug(
            "Replaced %r tag with p tag: %r",
            tag_type,
            tostring(monospaced, encoding="unicode"),
        )


def update_links(content: HtmlElement, language_slug: str) -> None:
    """
    Super method that gathers all methods related to updating links

    :param content: The content whose links should be updated
    :param language_slug: Slug of the current language
    """
    set_classes_for_links(content)
    remove_target_attribute(content)
    update_internal_links(content, language_slug)


def set_classes_for_links(content: HtmlElement) -> None:
    """
    Set class ``link-external`` for links

    :param content: the body of content of which the link classes should be adjusted.
    """
    for link in content.iter("a"):
        if href := link.get("href"):
            is_external = not any(url in href for url in settings.INTERNAL_URLS)
            if "link-external" not in link.classes and is_external:
                link.classes.add("link-external")
                logging.debug(
                    "Added class 'link-external' to %r",
                    tostring(link, encoding="unicode"),
                )
            elif "link-external" in link.classes and not is_external:
                link.classes.remove("link-external")
                logging.debug(
                    "Removed class 'link-external' from %r",
                    tostring(link, encoding="unicode"),
                )


def remove_target_attribute(content: HtmlElement) -> None:
    """
    Removes the target attribute of links if these links are external links

    :param content: the body of content of which the link targets should be removed
    """
    for link in content.iter("a"):
        link.attrib.pop("target", None)
        logging.debug(
            "Removed target attribute from link: %r",
            tostring(link, encoding="unicode"),
        )


def update_internal_links(content: HtmlElement, language_slug: str) -> None:
    """
    Updates internal links by adding the language slug of the translation

    :param content: the body of content of which the internal links should be updated
    :param language_slug: Slug of the current language
    """
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
                logging.debug("Updated link url from %s to %s", href, translated_url)


def process_images(content: HtmlElement) -> None:
    """
    This function processes images by scanning for media files and replacing alt texts.

    :param content: The body of content of which the images should be processed.
    """
    for image in content.iter("img"):
        if src := image.attrib.get("src"):
            logging.debug("Image tag found in content (src: %s)", src)
            # Remove host
            relative_url = urlparse(src).path
            # Remove media url prefix if exists
            if relative_url.startswith(settings.MEDIA_URL):
                relative_url = relative_url[len(settings.MEDIA_URL) :]
            # Check whether media file exists in database
            media_file = MediaFile.objects.filter(
                Q(file=relative_url) | Q(thumbnail=relative_url)
            ).first()
            # Replace alternative text
            if media_file and media_file.alt_text:
                logging.debug("Image alt text replaced: %r", media_file.alt_text)
                image.attrib["alt"] = media_file.alt_text
        else:
            logging.warning("Empty img tag was found.")
