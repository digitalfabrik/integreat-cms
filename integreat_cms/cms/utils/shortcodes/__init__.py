"""
This package contains the shortcodes which reference other objects from the content of a
translation, and the conversions between those shortcodes and the html they represent.

References are stored as shortcodes so that they are only resolved when the content is
requested (see ``ADR/0001-compose-referenced-objects-into-content-dynamically-shortcodes.md``).
That happens in two flavours:

* :func:`~integreat_cms.cms.utils.shortcodes.expand_shortcodes_for_delivery` builds the
  representation which is delivered to end users
* :func:`~integreat_cms.cms.utils.shortcodes.expand_shortcodes_for_cms` builds the
  representation which is presented to users of the CMS, because editors should not have to
  care about shortcodes at all

Whatever the CMS gets back is turned into shortcodes again by
:func:`~integreat_cms.cms.utils.shortcodes.collapse_into_shortcodes`, so that references to
internal content never reach the link index kept by our ``linkcheck`` dependency.

All three are implemented by the shortcodes themselves, see
:class:`~integreat_cms.cms.utils.shortcodes.base.Shortcode` and
:class:`~integreat_cms.cms.utils.shortcodes.base.EditableShortcode`.
"""

from __future__ import annotations

import logging
from functools import cache
from typing import TYPE_CHECKING

import shortcodes

from .base import EditableShortcode, registered_shortcodes

if TYPE_CHECKING:
    from typing import Any

    from lxml.html import HtmlElement

    from .base import Shortcode

logger = logging.getLogger(__name__)


@cache
def get_shortcodes() -> tuple[Shortcode, ...]:
    """
    Get all registered shortcodes.

    The modules which define them are imported here instead of at the top of this module,
    because a shortcode may need anything from the models to the content utils, which in turn
    need this module to collapse content into shortcodes.

    :return: The registered shortcodes
    """
    from . import contact, page

    return registered_shortcodes()


@cache
def _delivery_parser() -> shortcodes.Parser:
    """
    Get the parser which expands shortcodes into the content delivered to end users

    :return: The parser
    """
    parser = _build_parser()
    for shortcode in get_shortcodes():
        parser.register(shortcode.expand, shortcode.keyword)
        if shortcode.block_keyword:
            parser.register(
                shortcode.expand_block,
                shortcode.block_keyword,
                shortcode.block_end_keyword,
            )
    return parser


@cache
def _editable_shortcodes() -> tuple[EditableShortcode, ...]:
    """
    Get the shortcodes which are hidden from the users of the CMS

    :return: The editable shortcodes
    """
    return tuple(
        shortcode
        for shortcode in get_shortcodes()
        if isinstance(shortcode, EditableShortcode)
    )


@cache
def _cms_parser() -> shortcodes.Parser:
    """
    Get the parser which expands shortcodes into the content presented in the CMS.

    Shortcodes which are not editable are not registered at all, so that they are kept
    verbatim instead of being expanded into something the CMS could not collapse again.

    :return: The parser
    """
    parser = _build_parser()
    for shortcode in _editable_shortcodes():
        parser.register(shortcode.expand_for_cms, shortcode.keyword)
        if shortcode.block_keyword:
            parser.register(
                shortcode.expand_block_for_cms,
                shortcode.block_keyword,
                shortcode.block_end_keyword,
            )
    return parser


def _build_parser() -> shortcodes.Parser:
    """
    Build an empty parser which uses our shortcode syntax

    :return: The parser
    """
    return shortcodes.Parser(
        start="[",
        end="]",
        esc="\\",
        inherit_globals=False,
        ignore_unknown=True,
    )


def expand_shortcodes_for_delivery(
    content: str,
    context: dict[str, Any] | None = None,
) -> str:
    """
    Replace all shortcodes in ``content`` by the representation delivered to end users

    :param content: The content as it is stored in the database
    :param context: The context the shortcodes are expanded in
    :return: The expanded content
    """
    try:
        return _delivery_parser().parse(content, context)
    except shortcodes.ShortcodeError:
        logger.warning(
            "Failed expanding shortcodes in %r\ncontext: %r",
            content,
            context,
            exc_info=True,
        )
        # The best way to fail gracefully is to keep the content as it is
        return content


def expand_shortcodes_for_cms(content: str, language_slug: str) -> str:
    """
    Replace all editable shortcodes in ``content`` by the html they are edited as.

    Shortcodes which cannot be resolved are kept verbatim, so that editing content with a
    broken reference does not silently drop that reference.

    :param content: The content as it is stored in the database
    :param language_slug: The slug of the language the content should be presented in
    :return: The content with expanded references
    """
    try:
        return _cms_parser().parse(content, {"language_slug": language_slug})
    except shortcodes.ShortcodeError:
        logger.warning(
            "Failed expanding shortcodes for the CMS in %r",
            content,
            exc_info=True,
        )
        # The best way to fail gracefully is to keep the content as it is
        return content


def collapse_into_shortcodes(content: HtmlElement) -> None:
    """
    Replace everything in ``content`` which references another object by its shortcode.

    The tree is walked once and every element is passed through the cheap predicate of every
    editable shortcode, so that only elements which really might be a reference cause the
    database lookups needed to resolve them.

    :param content: The content which should be collapsed
    """
    editable = _editable_shortcodes()
    for element in list(content.iter()):
        for shortcode in editable:
            if shortcode.matches(element) and shortcode.collapse(element):
                break
