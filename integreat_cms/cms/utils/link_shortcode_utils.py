"""
This file contains utility functions to convert between links to internal content and the
shortcodes which represent them.

Internal references are stored as shortcodes so that they are only resolved when the content
is delivered (see ``ADR/0001-compose-referenced-objects-into-content-dynamically-shortcodes.md``).
This means the link index kept by our ``linkcheck`` dependency never has to know about them.

Editors should not have to care about that, so the shortcodes are expanded into ordinary
links whenever content is loaded into an editor (see
:func:`~integreat_cms.cms.utils.link_shortcode_utils.expand_link_shortcodes`) and collapsed
back into shortcodes whenever content is saved (see
:func:`~integreat_cms.cms.utils.link_shortcode_utils.collapse_links_to_shortcodes`).
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING

import shortcodes
from lxml.etree import LxmlError
from lxml.html import Element, fromstring, tostring

from ..models import Page
from .internal_link_utils import get_page_for_link

if TYPE_CHECKING:
    from typing import Any, Final

    from lxml.html import HtmlElement

    from ..models.pages.page_translation import PageTranslation

logger = logging.getLogger(__name__)

#: The keyword of the atomic shortcode which links to a page
PAGE_KEYWORD: Final[str] = "page"

#: The keyword of the block scoped shortcode which wraps its content in a link to a page
PAGE_LINK_KEYWORD: Final[str] = "page_link"

#: The keyword which closes :data:`PAGE_LINK_KEYWORD`
PAGE_LINK_END_KEYWORD: Final[str] = "/page_link"

#: The attribute which marks a link whose text should follow the title of its target
AUTO_UPDATE_ATTRIBUTE: Final[str] = "data-integreat-auto-update"

#: Characters which must not appear in a quoted shortcode argument. ``"``, ``\``, ``[`` and
#: ``]`` confuse the shortcode parser, which stops at the first closing delimiter and does not
#: unescape anything inside quotes. ``&``, ``<`` and ``>`` are html escaped when the content is
#: serialized, which would pile up another layer of escaping on every save.
#: Link texts containing any of them use the block scoped shortcode instead, whose content is
#: html and therefore not affected.
UNQUOTABLE_CHARACTERS: Final[frozenset[str]] = frozenset('"\\[]&<>')


def format_page_shortcode(page_id: int, text: str | None = None) -> str:
    """
    Build the atomic shortcode which links to a page

    :param page_id: The id of the :class:`~integreat_cms.cms.models.pages.page.Page` to link to
    :param text: The link text, or ``None`` to let the link follow the title of its target
    :return: The shortcode
    """
    if text is None:
        return f"[{PAGE_KEYWORD} {page_id}]"
    return f'[{PAGE_KEYWORD} {page_id} "{text}"]'


def format_page_link_shortcode(page_id: int, content: str) -> str:
    """
    Build the block scoped shortcode which wraps ``content`` in a link to a page

    :param page_id: The id of the :class:`~integreat_cms.cms.models.pages.page.Page` to link to
    :param content: The inner html of the link
    :return: The shortcode
    """
    return f"[{PAGE_LINK_KEYWORD} {page_id}]{content}[{PAGE_LINK_END_KEYWORD}]"


def get_editor_page_translation(
    page_id: str | int | None,
    language_slug: str | None,
) -> PageTranslation | None:
    """
    Get the page translation a link shortcode should point to while the content is edited.

    In contrast to the delivered content, the editor also has to be able to show links to
    pages which are not public (yet), because it is possible to insert such links.

    :param page_id: The id of the referenced :class:`~integreat_cms.cms.models.pages.page.Page`
    :param language_slug: The slug of the language the content is edited in
    :return: The referenced translation, or ``None`` if it cannot be resolved
    """
    if not page_id or not language_slug:
        return None
    try:
        page = Page.objects.get(id=page_id)
    except (Page.DoesNotExist, TypeError, ValueError):
        logger.debug(
            "Page with id=%r referenced by a shortcode does not exist", page_id
        )
        return None
    return (
        page.get_translation(language_slug)
        or page.get_public_translation(language_slug)
        or page.best_translation
    )


def expand_link_shortcodes(content: str, language_slug: str) -> str:
    """
    Replace all link shortcodes in ``content`` by the link they represent.

    Shortcodes which cannot be resolved are kept verbatim, so that editing content with a
    broken reference does not silently drop that reference.

    :param content: The content as it is stored in the database
    :param language_slug: The slug of the language the content should be presented in
    :return: The content with expanded links
    """
    try:
        return _link_parser.parse(content, {"language_slug": language_slug})
    except shortcodes.ShortcodeError:
        logger.warning(
            "Failed expanding link shortcodes in %r",
            content,
            exc_info=True,
        )
        # The best way to fail gracefully is to keep the content as it is
        return content


def collapse_links_to_shortcodes(content: HtmlElement) -> None:
    """
    Replace all links to internal pages in ``content`` by the shortcode representing them

    :param content: The content whose links should be collapsed
    """
    for link in list(content.iter("a")):
        collapse_link_to_shortcode(link)


def collapse_link_to_shortcode(link: HtmlElement) -> bool:
    """
    Replace ``link`` by the shortcode representing it, if it points to an internal page.

    Which shortcode is used depends on the content of the link:

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

    :param link: The link which should be collapsed
    :return: Whether the link was replaced
    """
    if not (page := get_page_for_link(link.get("href", ""))):
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
        opening, closing, children = format_page_shortcode(page.id), "", []
    elif not children and not UNQUOTABLE_CHARACTERS.intersection(text):
        opening, closing = format_page_shortcode(page.id, text), ""
    elif not children:
        opening, closing = format_page_link_shortcode(page.id, text), ""
    else:
        # The children have to stay elements of the content, so the block scoped shortcode
        # is split into the text around them
        opening = f"[{PAGE_LINK_KEYWORD} {page.id}]{text}"
        closing = f"[{PAGE_LINK_END_KEYWORD}]"

    parent.remove(link)
    for offset, child in enumerate(children):
        parent.insert(index + offset, child)
    if children:
        children[-1].tail = (children[-1].tail or "") + closing + tail
        _append_text_before(parent, index, opening)
    else:
        _append_text_before(parent, index, opening + closing + tail)

    logger.debug("Collapsed link to %r into a shortcode", page)
    return True


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


def _set_inner_html(element: HtmlElement, inner_html: str) -> None:
    """
    Set the content of ``element`` to the given html string

    :param element: The element whose content should be set
    :param inner_html: The html to insert into the element
    """
    try:
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


def _render_link(
    page_id: str | int | None,
    context: dict[str, Any] | None,
    text: str | None = None,
    inner_html: str | None = None,
) -> HtmlElement | None:
    """
    Render the link a shortcode represents while the content is edited

    :param page_id: The id of the referenced :class:`~integreat_cms.cms.models.pages.page.Page`
    :param context: The context the shortcode is expanded in
    :param text: The link text of the atomic shortcode, if it has one
    :param inner_html: The content of the block scoped shortcode, if it is used
    :return: The link, or ``None`` if the reference cannot be resolved
    """
    language_slug = (context or {}).get("language_slug")
    if not (translation := get_editor_page_translation(page_id, language_slug)):
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


def _unparse(keyword: str, pargs: list[str], kwargs: dict[str, str]) -> str:
    """
    Rebuild the source representation of a shortcode tag

    :param keyword: The keyword of the shortcode
    :param pargs: The positional arguments of the shortcode
    :param kwargs: The keyword arguments of the shortcode
    :return: The shortcode tag
    """
    # Everything but the id of the target is quoted, so that no quotes get lost while a
    # shortcode which cannot be resolved is kept verbatim
    arguments = [
        parg if index == 0 and parg and not any(map(str.isspace, parg)) else f'"{parg}"'
        for index, parg in enumerate(pargs)
    ]
    arguments += [f'{key}="{value}"' for key, value in kwargs.items()]
    return f"[{' '.join([keyword, *arguments])}]"


def _expand_page(
    pargs: list[str],
    kwargs: dict[str, str],
    context: dict[str, Any] | None,
) -> str:
    """
    Expand the atomic ``page`` shortcode into a link

    :param pargs: The positional arguments of the shortcode
    :param kwargs: The keyword arguments of the shortcode
    :param context: The context the shortcode is expanded in
    :return: The link, or the shortcode itself if it cannot be resolved
    """
    text = pargs[1] if len(pargs) > 1 else None
    if (link := _render_link(pargs[0] if pargs else None, context, text=text)) is None:
        return _unparse(PAGE_KEYWORD, pargs, kwargs)
    return tostring(link, encoding="unicode", with_tail=False)


def _expand_page_link(
    pargs: list[str],
    kwargs: dict[str, str],
    context: dict[str, Any] | None,
    content: str = "",
) -> str:
    """
    Expand the block scoped ``page_link`` shortcode into a link around its content

    :param pargs: The positional arguments of the shortcode
    :param kwargs: The keyword arguments of the shortcode
    :param context: The context the shortcode is expanded in
    :param content: The content enclosed by the shortcode
    :return: The link, or the shortcode itself if it cannot be resolved
    """
    if (
        link := _render_link(pargs[0] if pargs else None, context, inner_html=content)
    ) is None:
        return (
            _unparse(PAGE_LINK_KEYWORD, pargs, kwargs)
            + content
            + f"[{PAGE_LINK_END_KEYWORD}]"
        )
    return tostring(link, encoding="unicode", with_tail=False)


#: Parser which only knows the link shortcodes and passes everything else through unchanged
_link_parser = shortcodes.Parser(
    start="[",
    end="]",
    esc="\\",
    inherit_globals=False,
    ignore_unknown=True,
)
_link_parser.register(_expand_page, PAGE_KEYWORD)
_link_parser.register(_expand_page_link, PAGE_LINK_KEYWORD, PAGE_LINK_END_KEYWORD)
