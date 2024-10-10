import logging
import re
from copy import deepcopy
from html import unescape
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.db.models import Q
from django.template import loader
from lxml.etree import LxmlError
from lxml.html import Element, fromstring, HtmlElement, tostring

from ..models import Contact, MediaFile
from ..utils import internal_link_utils
from ..utils.link_utils import fix_content_link_encoding

logger = logging.getLogger(__name__)


def clean_content(content: str, language_slug: str) -> str:
    """
    This is the super function to clean content

    :param content: the body of content that should be cleaned
    :param language_slug: Slug of the current language
    """
    try:
        content = fromstring(content)
    except LxmlError:
        # The content is not guaranteed to be valid html, for example it may be empty
        return content

    convert_heading(content)
    convert_monospaced_tags(content)
    update_links(content, language_slug)
    fix_alt_texts(content)
    fix_notranslate(content)
    hide_anchor_tag_around_image(content)
    update_contacts(content)

    content_str = tostring(content, encoding="unicode", with_tail=False)
    return fix_content_link_encoding(content_str)


def convert_heading(content: HtmlElement) -> None:
    """
    Converts every ``h1`` tag in the content to a ``h2`` for SEO purposes.

    :param content: the body of content of which every ``h1`` should be converted to an ``h2``.
    """
    for heading in content.iter("h1"):
        heading.tag = "h2"
        logger.debug(
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
        logger.debug(
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
    for link in content.iter("a"):
        mark_external_links(link)
        remove_target_attribute(link)
        update_internal_links(link, language_slug)


def mark_external_links(link: HtmlElement) -> None:
    """
    Set class ``link-external`` for links

    :param link: the link which classes should be adjusted.
    """
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


def remove_target_attribute(link: HtmlElement) -> None:
    """
    Removes the target attribute of links if these links are external links

    :param link: links whose targets should be removed
    """
    link.attrib.pop("target", None)
    logger.debug(
        "Removed target attribute from link: %r",
        tostring(link, encoding="unicode"),
    )


def update_internal_links(link: HtmlElement, language_slug: str) -> None:
    """
    Fixes broken internal links

    :param link: link which should be checked for an internal link and then be updated
    :param language_slug: Slug of the current language
    """
    if translation := internal_link_utils.update_link(link, language_slug):
        new_url, new_html = translation
        if new_url != unquote(link.get("href", "")):
            link.set("href", new_url)
            logger.debug("Updated link url from %s to %s", link.get("href"), new_url)

        if new_html is not None:
            logger.debug("Updated link text from %s to %s", link.text, new_html)
            for child in link:
                link.remove(child)
            if isinstance(new_html, str):
                link.text = unescape(new_html)
            else:
                link.text = ""
                link.append(new_html)


def render_contact_card(contact_id: int, fetched_contacts: dict[int, Contact]) -> str:
    """
    Produces a rendered html element for the contact.

    :param contact_id: The id of the contact to render the card for
    :param fetched_contacts: A dictionary of pre-fetched contact objects, indexed by their id

    .. Note::

        This function does not fetch any contacts itself if the provided id is not in ``fetched_contacts``,
        nor will a contact at that key be double-checked to actually have the expected id.
        If the contact for the id is not provided, the contact will be assumed missing from our database and be labelled as invalid.
    """
    template = loader.get_template("contacts/contact_card.html")
    context = {
        "contact_id": contact_id,
        "contact": (
            fetched_contacts[contact_id] if contact_id in fetched_contacts else None
        ),
    }
    return template.render(context, None)


def update_contacts(content: HtmlElement, only_ids: tuple[int] | None = None) -> None:
    """
    Inject rendered contact html for given ID

    :param content: The content whose contacts should be updated
    :param only_ids: A list of ids if only certain contacts should be updated, otherwise None
    """
    nodes_to_update: dict[int, HtmlElement] = {}
    for div in content.iter("div"):
        children = list(div)
        match = None
        if (
            children
            and children[0].tag == "a"
            and (href := children[0].get("href", None))
        ):
            match = re.match(Contact.url_regex, href)
        if not match:
            continue

        try:
            contact_id = int(match.group(2))
        except ValueError:
            logger.warning("Failed parsing contact id %r as int", contact_id)

        if not isinstance(contact_id, int):
            logger.warning("Malformed contact id %r in content", contact_id)
        elif only_ids is None or contact_id in only_ids:
            # Gather all nodes
            if contact_id not in nodes_to_update:
                nodes_to_update[contact_id] = []
            nodes_to_update[contact_id].append(div)

    # Get all required contacts in a single query
    fetched_contacts = {
        contact.pk: contact
        for contact in Contact.objects.filter(id__in=nodes_to_update.keys())
    }

    for contact_id, divs in nodes_to_update.items():
        html = render_contact_card(contact_id, fetched_contacts=fetched_contacts)
        try:
            # We need the parsed form so we can plug it into our existing content tree
            new_div = fromstring(html)
        except LxmlError as e:
            logger.debug(
                "Failed to parse rendered HTML for contact card: %r\n→ %s\nEOF",
                e,
                html,
            )
            new_div = Element("pre", html)

        # Finally, inject the card in every occurence
        for div in divs:
            div.getparent().replace(div, deepcopy(new_div))


def fix_alt_texts(content: HtmlElement) -> None:
    """
    This function processes images by scanning for media files and replacing alt texts.

    :param content: The body of content of which the images should be processed.
    """
    for image in content.iter("img"):
        if src := image.attrib.get("src"):
            logger.debug("Image tag found in content (src: %s)", src)
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
                logger.debug("Image alt text replaced: %r", media_file.alt_text)
                image.attrib["alt"] = media_file.alt_text
        else:
            logger.warning("Empty img tag was found.")


def fix_notranslate(content: HtmlElement) -> None:
    """
    This function normalizes every notranslate tag,
    assuring ``notranslate`` class, ``translate`` attribute and ``dir=ltr`` are set.

    :param content: The body of content of which the notranslate markers should be processed.
    """
    for span in content.iter("span"):
        if "notranslate" in span.classes or span.attrib.get("translate") == "no":
            logger.debug("Notranslate found in content")
            span.classes.add("notranslate")
            span.attrib.update(
                {
                    "translate": "no",
                    "dir": "ltr",
                }
            )


def hide_anchor_tag_around_image(content: HtmlElement) -> None:
    """
    This function checks whether an image tag wrapped by an anchor tag has an empty alt tag, if so it hides anchor tag from screen-reader and tab-key

    :param content: the content which has an anchor tag wrapped around an img tag
    """

    for anchor in content.iter("a"):
        children = list(anchor.iterchildren())

        # Check if the anchor tag has only img children and no other text content
        if (
            len(children) == 1
            and (img := children[0]).tag == "img"
            and not anchor.text_content().strip()
        ):
            if img.attrib.get("alt", ""):
                if "aria-hidden" in anchor.attrib:
                    del anchor.attrib["aria-hidden"]
                    logger.debug(
                        "Removed 'aria-hidden' from anchor: %r",
                        tostring(anchor, encoding="unicode"),
                    )
                if "tabindex" in anchor.attrib:
                    del anchor.attrib["tabindex"]
                    logger.debug(
                        "Removed 'tabindex' from anchor: %r",
                        tostring(anchor, encoding="unicode"),
                    )
            else:
                # Hide the anchor tag by setting aria-hidden attribute if the image alt text is empty
                anchor.set("aria-hidden", "true")
                logger.debug(
                    "Set 'aria-hidden' to true for anchor: %r",
                    tostring(anchor, encoding="unicode"),
                )
                # Unfocus the anchor tag from tab key
                anchor.set("tabindex", "-1")
                logger.debug(
                    "Set 'tabindex' to -1 for anchor: %r",
                    tostring(anchor, encoding="unicode"),
                )
