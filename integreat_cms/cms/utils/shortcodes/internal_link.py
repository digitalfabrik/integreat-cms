"""
This module contains everything shortcodes which reference internal content by a link have
in common. Adding such a shortcode for another kind of content is a matter of declaring the
model it references and how its urls look, see
:class:`~integreat_cms.cms.utils.shortcodes.internal_link.InternalLinkShortcode`.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

from django.utils.translation import gettext_lazy as _
from lxml.etree import LxmlError
from lxml.html import Element, fromstring, tostring

from ..content_utils import hide_anchor_tag_around_single_image
from ..internal_link_utils import SHORT_LINKS_NETLOC, WEBAPP_NETLOC
from .base import EditableShortcode

if TYPE_CHECKING:
    from typing import Any, ClassVar, Final

    from lxml.html import HtmlElement

    from ...models.abstract_content_model import AbstractContentModel
    from ...models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)

#: The attribute which marks a link whose text should follow the title of its target
AUTO_UPDATE_ATTRIBUTE: Final[str] = "data-integreat-auto-update"

#: Characters which must not appear in a quoted shortcode argument. ``"``, ``\``, ``[`` and
#: ``]`` confuse the shortcode parser, which stops at the first closing delimiter and does not
#: unescape anything inside quotes. ``&``, ``<`` and ``>`` are html escaped when the content is
#: serialized, which would pile up another layer of escaping on every save.
#: Link texts containing any of them use the block scoped shortcode instead, whose content is
#: html and therefore not affected.
UNQUOTABLE_CHARACTERS: Final[frozenset[str]] = frozenset('"\\[]&<>')


class InternalLinkShortcode(EditableShortcode):
    """
    A shortcode which references internal content by a link.

    Both forms of the shortcode are used, depending on what the link contains:

    .. list-table::
        :widths: 55 45
        :header-rows: 1

        * - Link
          - Shortcode
        * - ``<a href="…" data-integreat-auto-update="true">Willkommen</a>``
          - ``[page 1]``
        * - ``<a href="…">hier</a>``
          - ``[page 1 "hier"]``
        * - ``<a href="…"><img src="…"></a>``
          - ``[page_link 1]<img src="…">[/page_link]``

    Subclasses only declare which content they reference and how its urls look::

        @register
        class EventShortcode(InternalLinkShortcode):
            keyword = "event"
            block_keyword = "event_link"
            model = Event
            url_infix = "events"
    """

    #: The model of the content this shortcode references
    model: ClassVar[type[AbstractContentModel]]

    #: The path segment which distinguishes webapp urls to this content from urls to other
    #: content, for example ``events`` in ``/augsburg/de/events/test-veranstaltung/``
    url_infix: ClassVar[str | None] = None

    #: The path segment which identifies this content in short urls, for example ``p`` in
    #: ``/s/p/42/``, or ``None`` if this content has no short urls
    short_url_infix: ClassVar[str | None] = None

    def matches_url_infix(self, infix: str) -> bool:
        """
        Whether the first path segment after region and language belongs to this content

        :param infix: The path segment
        :return: Whether a url with this segment points to this kind of content
        """
        return infix == self.url_infix

    def format_shortcode(self, object_id: int, text: str | None = None) -> str:
        """
        Build the atomic shortcode which links to the given object

        :param object_id: The id of the object to link to
        :param text: The link text, or ``None`` to let the link follow the title of its target
        :return: The shortcode
        """
        if text is None:
            return f"[{self.keyword} {object_id}]"
        return f'[{self.keyword} {object_id} "{text}"]'

    def format_block_shortcode(self, object_id: int, content: str) -> str:
        """
        Build the block scoped shortcode which wraps ``content`` in a link to the given object

        :param object_id: The id of the object to link to
        :param content: The inner html of the link
        :return: The shortcode
        """
        return f"[{self.block_keyword} {object_id}]{content}[{self.block_end_keyword}]"

    # Expansion into the content which is delivered to end users

    def expand(
        self,
        pargs: list[str],
        kwargs: dict[str, str],  # noqa: ARG002
        context: dict[str, Any] | None,
    ) -> str:
        """
        Expand the atomic form into a link to the public translation of its target

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :return: The link, or a marker that the reference is broken
        """
        text = pargs[1] if len(pargs) > 1 else None
        if (translation := self._get_public_translation(pargs, context)) is None:
            element = _missing_link(text or "")
        else:
            element = _render_link(translation, text)
        return tostring(element).decode("utf-8")

    def expand_block(
        self,
        pargs: list[str],
        kwargs: dict[str, str],  # noqa: ARG002
        context: dict[str, Any] | None,
        content: str = "",
    ) -> str:
        """
        Expand the block scoped form into a link around its content

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :param content: The content enclosed by the shortcode
        :return: The link, or a marker that the reference is broken
        """
        if (translation := self._get_public_translation(pargs, context)) is None:
            element = _missing_link(content)
        else:
            element = _render_link(translation, content)
        return tostring(element).decode("utf-8")

    def _get_public_translation(
        self,
        pargs: list[str],
        context: dict[str, Any] | None,
    ) -> AbstractContentTranslation | None:
        """
        Get the public translation this shortcode refers to

        :param pargs: The positional arguments of the shortcode, the first of which is the id
                      of the referenced object
        :param context: The context the shortcode is expanded in
        :return: The public translation which is linked to, or ``None`` if it cannot be resolved
        """
        if (referenced := self._get_object_by_id(pargs[0] if pargs else None)) is None:
            return None
        language_slug = (context or {}).get(
            "language_slug",
            referenced.region.default_language.slug,
        )
        return referenced.get_public_translation(language_slug)

    # Expansion into the content which is edited in the CMS

    def expand_for_cms(
        self,
        pargs: list[str],
        kwargs: dict[str, str],
        context: dict[str, Any] | None,
    ) -> str:
        """
        Expand the atomic form into the link which is loaded into the editor

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :return: The link, or the shortcode itself if it cannot be resolved
        """
        text = pargs[1] if len(pargs) > 1 else None
        if (link := self._render_editor_link(pargs, context, text=text)) is None:
            return self.unparse(pargs, kwargs)
        return tostring(link, encoding="unicode", with_tail=False)

    def expand_block_for_cms(
        self,
        pargs: list[str],
        kwargs: dict[str, str],
        context: dict[str, Any] | None,
        content: str = "",
    ) -> str:
        """
        Expand the block scoped form into the link which is loaded into the editor

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :param content: The content enclosed by the shortcode
        :return: The link, or the shortcode itself if it cannot be resolved
        """
        link = self._render_editor_link(pargs, context, inner_html=content)
        if link is None:
            return self.unparse_block(pargs, kwargs, content)
        return tostring(link, encoding="unicode", with_tail=False)

    def _render_editor_link(
        self,
        pargs: list[str],
        context: dict[str, Any] | None,
        text: str | None = None,
        inner_html: str | None = None,
    ) -> HtmlElement | None:
        """
        Render the link this shortcode represents while the content is edited

        :param pargs: The positional arguments of the shortcode, the first of which is the id
                      of the referenced object
        :param context: The context the shortcode is expanded in
        :param text: The link text of the atomic form, if it has one
        :param inner_html: The content of the block scoped form, if it is used
        :return: The link, or ``None`` if the reference cannot be resolved
        """
        language_slug = (context or {}).get("language_slug")
        translation = self._get_editor_translation(
            pargs[0] if pargs else None,
            language_slug,
        )
        if translation is None:
            return None

        link = Element("a")
        link.set("href", translation.full_url)
        if inner_html is not None:
            _set_inner_html(link, inner_html)
        elif text is None:
            # Without an explicit link text, the link follows the title of its target
            link.set(AUTO_UPDATE_ATTRIBUTE, "true")
            _set_link_title(link, translation.link_title)
        else:
            link.text = text
        return link

    def _get_editor_translation(
        self,
        object_id: str | int | None,
        language_slug: str | None,
    ) -> AbstractContentTranslation | None:
        """
        Get the translation this shortcode should point to while the content is edited.

        In contrast to the delivered content, the editor also has to be able to show links to
        content which is not public (yet), because it is possible to insert such links.

        :param object_id: The id of the referenced object
        :param language_slug: The slug of the language the content is edited in
        :return: The referenced translation, or ``None`` if it cannot be resolved
        """
        if not language_slug:
            return None
        if (referenced := self._get_object_by_id(object_id)) is None:
            return None
        return (
            referenced.get_translation(language_slug)
            or referenced.get_public_translation(language_slug)
            or referenced.best_translation
        )

    def _get_object_by_id(
        self,
        object_id: str | int | None,
    ) -> AbstractContentModel | None:
        """
        Get the object a shortcode references by its id

        :param object_id: The id of the referenced object
        :return: The referenced object, or ``None`` if it does not exist
        """
        if not object_id:
            return None
        try:
            return self.model.objects.get(id=object_id)
        except (self.model.DoesNotExist, TypeError, ValueError):
            logger.debug(
                "%s with id=%r referenced by a shortcode does not exist",
                self.model.__name__,
                object_id,
            )
            return None

    # Collapsing the content which was edited in the CMS

    def matches(self, element: HtmlElement) -> bool:
        """
        Whether ``element`` is a link whose url looks like it points to this kind of content

        :param element: The element to check
        :return: Whether the element is a candidate for being collapsed
        """
        return element.tag == "a" and self._references(element.get("href", ""))

    def _references(self, url: str) -> bool:
        """
        Whether ``url`` points to this kind of content, judged by its shape alone

        :param url: The url to check
        :return: Whether the url might point to this kind of content
        """
        if not url:
            return False
        parsed_url = urlparse(url)
        if parsed_url.netloc == WEBAPP_NETLOC:
            return self._webapp_path_parts(parsed_url.path) is not None
        if parsed_url.netloc == SHORT_LINKS_NETLOC:
            return self._short_link_translation_id(parsed_url.path) is not None
        return False

    def collapse(self, link: HtmlElement) -> bool:
        """
        Replace ``link`` by the shortcode representing it, if it points to this kind of content.

        The children of the link have to stay elements of the content, so a link which contains
        markup is not replaced by a single text node but by the opening and closing tag of the
        block scoped shortcode around its children.

        :param link: The link which should be collapsed
        :return: Whether the link was replaced
        """
        if not (referenced := self.get_object_for_url(link.get("href", ""))):
            return False
        if (parent := link.getparent()) is None:
            logger.debug("Cannot collapse link %r without a parent element", link)
            return False

        index = parent.index(link)
        tail = link.tail or ""
        text = link.text or ""
        children = list(link)

        if link.get(AUTO_UPDATE_ATTRIBUTE) == "true":
            # The link follows the title of its target, so its current content is irrelevant
            opening, closing, children = self.format_shortcode(referenced.id), "", []
        elif not children and not UNQUOTABLE_CHARACTERS.intersection(text):
            opening, closing = self.format_shortcode(referenced.id, text), ""
        elif not children:
            opening, closing = self.format_block_shortcode(referenced.id, text), ""
        else:
            opening = f"[{self.block_keyword} {referenced.id}]{text}"
            closing = f"[{self.block_end_keyword}]"

        parent.remove(link)
        for offset, child in enumerate(children):
            parent.insert(index + offset, child)
        if children:
            children[-1].tail = (children[-1].tail or "") + closing + tail
            _append_text_before(parent, index, opening)
        else:
            _append_text_before(parent, index, opening + closing + tail)

        logger.debug("Collapsed link to %r into a shortcode", referenced)
        return True

    def get_object_for_url(self, url: str) -> AbstractContentModel | None:
        """
        Get the object an internal url points to.

        In contrast to :func:`~integreat_cms.cms.utils.internal_link_utils.get_public_translation_for_link`,
        this does not care about the publication status of the target, because links to content
        which is not public (yet) have to be recognized as internal references as well.

        :param url: The url
        :return: The referenced object, or ``None`` if the url does not point to one
        """
        if not url:
            return None
        parsed_url = urlparse(url)
        if parsed_url.netloc == WEBAPP_NETLOC:
            if (parts := self._webapp_path_parts(parsed_url.path)) is None:
                return None
            region_slug, language_slug, *path_parts = parts
            return self._get_object_for_webapp_link(
                region_slug,
                language_slug,
                path_parts,
            )
        if parsed_url.netloc == SHORT_LINKS_NETLOC:
            if (
                translation_id := self._short_link_translation_id(parsed_url.path)
            ) is None:
                return None
            return self.model.objects.filter(translations__id=translation_id).first()
        return None

    def _webapp_path_parts(self, path: str) -> list[str] | None:
        """
        Split the path of a webapp url into its parts, if it points to this kind of content

        :param path: The url path, for example ``/augsburg/de/willkommen/``
        :return: The path parts, or ``None`` if the path does not point to this content
        """
        parts: list[str] = unquote(path).strip("/").split("/")
        if len(parts) < 3 or not self.matches_url_infix(parts[2]):
            # Not a link to a specific piece of this kind of content
            return None
        return parts

    def _short_link_translation_id(self, path: str) -> int | None:
        """
        Get the id of the translation a short url path points to

        :param path: The url path, for example ``/s/p/124/``
        :return: The id of the referenced translation, or ``None`` if the path does not
                 point to this kind of content
        """
        parts: list[str] = unquote(path).strip("/").split("/")
        if len(parts) != 3 or parts[0] != "s" or parts[1] != self.short_url_infix:
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

    def _get_object_for_webapp_link(
        self,
        region_slug: str,
        language_slug: str,
        path_parts: list[str],
    ) -> AbstractContentModel | None:
        """
        Get the object a webapp url points to

        :param region_slug: The slug of the region of the referenced content
        :param language_slug: The slug of the language of the url
        :param path_parts: The path parts after region and language,
                           for example ``["willkommen"]``
        :return: The referenced object, or ``None`` if it does not exist
        """
        referenced = self.model.objects.filter(
            region__slug=region_slug,
            translations__language__slug=language_slug,
            translations__slug=path_parts[-1],
        ).distinct()

        if len(referenced) < 2:
            return referenced.first()

        # The slug of a page is only unique among its siblings, so if the last path part is
        # ambiguous, prefer the object whose current url matches the whole path. Outdated urls
        # are still tolerated, because their slug is kept in the version history.
        path = "/".join([region_slug, language_slug, *path_parts])
        for candidate in referenced:
            if (
                translation := candidate.get_translation(language_slug)
            ) and translation.get_absolute_url().strip("/") == path:
                return candidate
        return referenced.first()


def _missing_link(inner_html: str) -> HtmlElement:
    """
    Build the replacement for a shortcode whose target cannot be resolved

    :param inner_html: The content of the link, if it has any
    :return: The element to insert instead of the link
    """
    TEXT_MISSING = _(
        "MISSING LINK"
    )  # Separate variable because gettext apparently does not find _() if it is in an f-string
    try:
        return fromstring(f"<i>[{inner_html or TEXT_MISSING}]</i>")
    except LxmlError:
        element = Element("i")
        element.text = f"[{TEXT_MISSING}]"
        return element


def _render_link(
    translation: AbstractContentTranslation,
    inner_html: str | None,
) -> HtmlElement:
    """
    Build the link to the given translation which is delivered to end users

    :param translation: The translation which is linked to
    :param inner_html: The content of the link, or ``None`` to use the link title of the target
    :return: The link element
    """
    element = Element("a")
    if inner_html is None:
        _set_link_title(element, translation.link_title)
    else:
        _set_inner_html(element, inner_html)
    # Absolute, because that is what internal links looked like before they were stored as
    # shortcodes: the content delivered to clients has always contained full webapp urls
    element.attrib["href"] = translation.full_url
    hide_anchor_tag_around_single_image(element)
    return element


def _set_inner_html(element: HtmlElement, inner_html: str) -> None:
    """
    Set the content of ``element`` to the given html string

    :param element: The element whose content should be set
    :param inner_html: The html to insert into the element
    """
    try:
        # LXML needs a single root element, so we're doing this in a roundabout way
        parsed = fromstring(f"<div>{inner_html}</div>")
    except LxmlError:
        logger.debug("Failed to parse inner html of a link: %r", inner_html)
        element.text = inner_html
        return
    element.text = parsed.text
    for child in parsed:
        element.append(child)


def _set_link_title(link: HtmlElement, link_title: HtmlElement | str) -> None:
    """
    Set the content of ``link`` to the link title of its target

    :param link: The link whose content should be set
    :param link_title: The :attr:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.link_title`
                       of the target, which is either an escaped string or an element with a tail
    """
    if isinstance(link_title, str):
        _set_inner_html(link, link_title)
    else:
        # The link title is cached on the translation, so it must not be re-parented
        link.append(deepcopy(link_title))


def _append_text_before(parent: HtmlElement, index: int, text: str) -> None:
    """
    Append ``text`` to the character data which precedes the child of ``parent`` at ``index``

    :param parent: The element whose character data should be extended
    :param index: The index of the child element the text should precede
    :param text: The text to append
    """
    if index == 0:
        parent.text = (parent.text or "") + text
    else:
        previous = parent[index - 1]
        previous.tail = (previous.tail or "") + text
