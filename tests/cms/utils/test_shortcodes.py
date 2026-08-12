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
        == '<p><a href="https://integreat.app/augsburg/de/willkommen/">Willkommen</a></p>'
    )


@pytest.mark.django_db
def test_page_shortcode_with_text(load_test_data: None) -> None:
    """
    A ``[page]`` shortcode with link text uses that text
    """
    assert (
        expand_shortcodes('<p>[page 1 "hier"]</p>', DE)
        == '<p><a href="https://integreat.app/augsburg/de/willkommen/">hier</a></p>'
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
        == '<p><a href="https://integreat.app/augsburg/de/willkommen/"><b>hier</b> lang</a></p>'
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
        '<p><a href="https://integreat.app/augsburg/de/willkommen/" aria-hidden="true" tabindex="-1">'
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


@pytest.mark.django_db
def test_content_for_delivery_expands_shortcodes(load_test_data: None) -> None:
    """
    A translation expands its own shortcodes with the context derived from itself
    """
    from integreat_cms.cms.models import PageTranslation

    translation = (
        PageTranslation.objects.filter(page_id=2, language__slug="de")
        .order_by("-version")
        .first()
    )
    PageTranslation.objects.filter(pk=translation.pk).update(
        content='<p>[page 1 "hier"]</p>',
    )
    translation.refresh_from_db()

    assert translation.content_for_delivery() == (
        '<p><a href="https://integreat.app/augsburg/de/willkommen/">hier</a></p>'
    )


@pytest.mark.django_db
def test_content_for_delivery_includes_mirrored_content(load_test_data: None) -> None:
    """
    Pages deliver the content of their mirrored page as well, so the shortcodes in there
    have to be expanded too
    """
    from integreat_cms.cms.models import Page, PageTranslation

    mirrored = Page.objects.get(id=1)
    PageTranslation.objects.filter(page_id=1, language__slug="de").update(
        content='<p>[page 1 "gespiegelt"]</p>',
    )

    page = Page.objects.get(id=2)
    page.mirrored_page = mirrored
    page.mirrored_page_first = False
    page.save()

    translation = (
        PageTranslation.objects.filter(page_id=2, language__slug="de")
        .order_by("-version")
        .first()
    )
    assert '<a href="https://integreat.app/augsburg/de/willkommen/">gespiegelt</a>' in (
        translation.content_for_delivery()
    )


@pytest.mark.django_db
def test_content_for_delivery_accepts_extra_context(load_test_data: None) -> None:
    """
    Context which cannot be derived from the translation can be passed in and wins over
    the derived context
    """
    from integreat_cms.cms.models import PageTranslation

    translation = (
        PageTranslation.objects.filter(page_id=2, language__slug="de")
        .order_by("-version")
        .first()
    )
    PageTranslation.objects.filter(pk=translation.pk).update(
        content="<p>[page 1]</p>",
    )
    translation.refresh_from_db()

    assert translation.content_for_delivery(language_slug="en") == (
        '<p><a href="https://integreat.app/augsburg/en/welcome/">Welcome</a></p>'
    )
