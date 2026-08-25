"""
Tests for the registry which bundles the three pieces every shortcode consists of
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from lxml.html import fromstring

from integreat_cms.cms.utils.shortcodes import (
    EditableShortcode,
    expand_shortcodes_for_cms,
    get_shortcodes,
)
from integreat_cms.cms.utils.shortcodes.page import PageShortcode

if TYPE_CHECKING:
    from collections.abc import Callable

    from lxml.html import HtmlElement

#: The full url of the German translation of page 1 in the Augsburg region
WILLKOMMEN_URL = "https://integreat.app/augsburg/de/willkommen/"


def parse(html: str) -> HtmlElement:
    """
    Parse a single html element, no matter whether it is a block level element or not

    :param html: The element to parse
    :return: The parsed element
    """
    return fromstring(f"<div>{html}</div>")[0]


def test_registry_contains_all_shortcodes() -> None:
    """
    Every module which defines a shortcode is loaded when the registry is used
    """
    assert {shortcode.keyword for shortcode in get_shortcodes()} == {"page", "contact"}


def test_only_editable_shortcodes_have_a_cms_representation() -> None:
    """
    A shortcode which references a page is hidden from the editor, a contact card is not
    """
    editable = {
        shortcode.keyword
        for shortcode in get_shortcodes()
        if isinstance(shortcode, EditableShortcode)
    }
    assert editable == {"page"}


@pytest.mark.django_db
def test_shortcodes_without_a_cms_representation_are_kept_verbatim(
    load_test_data: None,
) -> None:
    """
    Only editable shortcodes are expanded for the CMS, everything else is left untouched
    """
    assert expand_shortcodes_for_cms("<p>[contact 1 email]</p>", "de") == (
        "<p>[contact 1 email]</p>"
    )


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (f'<a href="{WILLKOMMEN_URL}">hier</a>', True),
        ('<a href="http://localhost:8000/s/p/1/">hier</a>', True),
        ('<a href="https://example.com/">extern</a>', False),
        (
            '<a href="https://integreat.app/augsburg/de/events/fest/">Fest</a>',
            False,
        ),
        ('<a href="https://integreat.app/augsburg/de/">Augsburg</a>', False),
        ('<a href="http://localhost:8000/s/i/1/">Impressum</a>', False),
        ("<a>ohne Ziel</a>", False),
        (f'<span data-href="{WILLKOMMEN_URL}">kein Link</span>', False),
    ],
)
def test_predicate_recognizes_links_to_pages(html: str, expected: bool) -> None:
    """
    The predicate accepts exactly those elements which might be a link to a page

    :param html: The element to check
    :param expected: Whether the predicate should accept it
    """
    assert PageShortcode().matches(parse(html)) is expected


@pytest.mark.django_db
def test_predicate_does_not_query_the_database(
    django_assert_num_queries: Callable,
) -> None:
    """
    The predicate is run for every element of every saved content, so it has to decide
    without touching the database. Only what it accepts is looked up by ``collapse``.

    :param django_assert_num_queries: The fixture providing the query assertion
    """
    elements = [
        parse(f'<a href="{WILLKOMMEN_URL}">hier</a>'),
        parse('<a href="https://example.com/">extern</a>'),
        parse("<p>kein Link</p>"),
    ]
    shortcode = PageShortcode()
    with django_assert_num_queries(0):
        for element in elements:
            shortcode.matches(element)
