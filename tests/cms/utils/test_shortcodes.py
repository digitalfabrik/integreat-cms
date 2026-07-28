"""
Tests for the shortcodes which are expanded when content is delivered
"""

from __future__ import annotations

import pytest
from django.utils import translation

from integreat_cms.cms.utils.shortcodes import expand_shortcodes

#: The context the shortcodes are expanded in
DE = {"language_slug": "de"}


@pytest.mark.django_db
def test_page_shortcode_without_text(load_test_data: None) -> None:
    """
    A ``[page]`` shortcode without link text uses the title of its target
    """
    assert (
        expand_shortcodes("<p>[page 1]</p>", DE)
        == '<p><a href="/augsburg/de/willkommen/">Willkommen</a></p>'
    )


@pytest.mark.django_db
def test_page_shortcode_with_text(load_test_data: None) -> None:
    """
    A ``[page]`` shortcode with link text uses that text
    """
    assert (
        expand_shortcodes('<p>[page 1 "hier"]</p>', DE)
        == '<p><a href="/augsburg/de/willkommen/">hier</a></p>'
    )


@pytest.mark.django_db
def test_page_shortcode_missing_target(load_test_data: None) -> None:
    """
    A ``[page]`` shortcode whose target does not exist is marked as a missing link
    """
    with translation.override("en"):
        assert (
            expand_shortcodes("<p>[page 999999]</p>", DE)
            == "<p><i>[MISSING LINK]</i></p>"
        )
    assert (
        expand_shortcodes('<p>[page 999999 "hier"]</p>', DE) == "<p><i>[hier]</i></p>"
    )


@pytest.mark.django_db
def test_page_link_shortcode(load_test_data: None) -> None:
    """
    A ``[page_link]`` shortcode wraps its content in a link to its target
    """
    assert (
        expand_shortcodes("<p>[page_link 1]<b>hier</b> lang[/page_link]</p>", DE)
        == '<p><a href="/augsburg/de/willkommen/"><b>hier</b> lang</a></p>'
    )


@pytest.mark.django_db
def test_page_link_shortcode_missing_target(load_test_data: None) -> None:
    """
    A ``[page_link]`` shortcode whose target does not exist keeps its content
    """
    assert (
        expand_shortcodes("<p>[page_link 999999]<b>hier</b>[/page_link]</p>", DE)
        == "<p><i>[<b>hier</b>]</i></p>"
    )


@pytest.mark.django_db
def test_page_link_shortcode_hides_linked_image_without_alt_text(
    load_test_data: None,
) -> None:
    """
    A link which only contains an image without alt text has to be hidden from screen
    readers and the tab key, just like the same link would be if it was part of the content
    """
    assert expand_shortcodes(
        '<p>[page_link 1]<img src="/media/test.png" alt="">[/page_link]</p>', DE
    ) == (
        '<p><a href="/augsburg/de/willkommen/" aria-hidden="true" tabindex="-1">'
        '<img src="/media/test.png" alt=""></a></p>'
    )


@pytest.mark.django_db
def test_page_link_shortcode_keeps_linked_image_with_alt_text(
    load_test_data: None,
) -> None:
    """
    A link around an image which has an alt text stays reachable
    """
    result = expand_shortcodes(
        '<p>[page_link 1]<img src="/media/test.png" alt="Willkommen">[/page_link]</p>',
        DE,
    )
    assert "aria-hidden" not in result
    assert "tabindex" not in result
