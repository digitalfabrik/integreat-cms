"""
This module contains the conversions between shortcodes and the html they represent, in all
three directions: expansion for delivery, expansion for the CMS and collapsing back into
shortcodes. All three are implemented by the shortcodes themselves, see
:class:`~integreat_cms.cms.utils.shortcodes.base.Shortcode` and
:class:`~integreat_cms.cms.utils.shortcodes.base.EditableShortcode`.
"""

from __future__ import annotations

import logging
from functools import cache
from typing import TYPE_CHECKING

import shortcodes

from .registry import editable_shortcodes, get_shortcodes

if TYPE_CHECKING:
    from typing import Any

    from lxml.html import HtmlElement

logger = logging.getLogger(__name__)


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
def _cms_parser() -> shortcodes.Parser:
    """
    Get the parser which expands shortcodes into the content presented in the CMS.

    Shortcodes which are not editable are not registered at all, so that they are kept
    verbatim instead of being expanded into something the CMS could not collapse again.

    :return: The parser
    """
    parser = _build_parser()
    for shortcode in editable_shortcodes():
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
    editable = editable_shortcodes()
    for element in list(content.iter()):
        for shortcode in editable:
            if shortcode.matches(element) and shortcode.collapse(element):
                break
