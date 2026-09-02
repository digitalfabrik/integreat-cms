"""
Tests for the conversion between internal links and their shortcode representation
"""

from __future__ import annotations

import pytest
from lxml.html import fromstring, tostring

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import PageTranslation
from integreat_cms.cms.utils.content_utils import clean_content
from integreat_cms.cms.utils.shortcodes import (
    collapse_into_shortcodes,
    expand_shortcodes_for_cms,
)

#: The full url of the German translation of page 1 in the Augsburg region
WILLKOMMEN_URL = "https://integreat.app/augsburg/de/willkommen/"

#: The full url of the German translation of page 3, a child of page 1
UBER_DIE_APP_URL = (
    "https://integreat.app/augsburg/de/willkommen/uber-die-app-integreat-augsburg/"
)


def unpublish_page_3() -> None:
    """
    Turn all German translations of page 3 into drafts,
    so that the page has no public translation in German anymore
    """
    PageTranslation.objects.filter(page_id=3, language__slug="de").update(
        status=status.DRAFT,
    )


def collapse(content: str) -> str:
    """
    Run :func:`~integreat_cms.cms.utils.shortcodes.conversion.collapse_into_shortcodes`
    on a html string and return the result as a html string again
    """
    element = fromstring(content)
    collapse_into_shortcodes(element)
    return tostring(element, encoding="unicode", with_tail=False)


@pytest.mark.django_db
def test_expand_page_shortcode_without_text(load_test_data: None) -> None:
    """
    A ``[page]`` shortcode without link text becomes an auto updating link
    """
    assert expand_shortcodes_for_cms("<p>[page 1]</p>", "de") == (
        f'<p><a href="{WILLKOMMEN_URL}" data-integreat-auto-update="true">Willkommen</a></p>'
    )


@pytest.mark.django_db
def test_expand_page_shortcode_with_text(load_test_data: None) -> None:
    """
    A ``[page]`` shortcode with link text becomes a plain link
    """
    assert expand_shortcodes_for_cms('<p>[page 1 "hier"]</p>', "de") == (
        f'<p><a href="{WILLKOMMEN_URL}">hier</a></p>'
    )


@pytest.mark.django_db
def test_expand_page_shortcode_uses_requested_language(load_test_data: None) -> None:
    """
    The shortcode is expanded to the url of the translation in the requested language
    """
    assert expand_shortcodes_for_cms("<p>[page 1]</p>", "en") == (
        '<p><a href="https://integreat.app/augsburg/en/welcome/"'
        ' data-integreat-auto-update="true">Welcome</a></p>'
    )


@pytest.mark.django_db
def test_expand_page_link_shortcode(load_test_data: None) -> None:
    """
    A ``[page_link]`` block shortcode wraps its content in a link
    """
    assert (
        expand_shortcodes_for_cms(
            '<p>[page_link 1]<img src="/media/test.png" alt="">[/page_link]</p>', "de"
        )
        == f'<p><a href="{WILLKOMMEN_URL}"><img src="/media/test.png" alt=""></a></p>'
    )


@pytest.mark.django_db
def test_expand_unresolvable_shortcode_is_kept_verbatim(load_test_data: None) -> None:
    """
    Shortcodes which cannot be resolved must survive the round trip untouched
    instead of silently vanishing from the content
    """
    assert (
        expand_shortcodes_for_cms("<p>[page 999999]</p>", "de")
        == "<p>[page 999999]</p>"
    )
    assert (
        expand_shortcodes_for_cms('<p>[page 999999 "hier"]</p>', "de")
        == '<p>[page 999999 "hier"]</p>'
    )
    assert (
        expand_shortcodes_for_cms("<p>[page_link 999999]<b>x</b>[/page_link]</p>", "de")
        == "<p>[page_link 999999]<b>x</b>[/page_link]</p>"
    )


@pytest.mark.django_db
def test_expand_leaves_other_shortcodes_alone(load_test_data: None) -> None:
    """
    Only link shortcodes are expanded, everything else is passed through
    """
    assert (
        expand_shortcodes_for_cms("<p>[contact 1 email]</p>", "de")
        == "<p>[contact 1 email]</p>"
    )


@pytest.mark.django_db
def test_expand_page_shortcode_to_draft_page(load_test_data: None) -> None:
    """
    Editors may link to pages which have no public translation yet,
    so those shortcodes must be expanded as well
    """
    unpublish_page_3()
    assert expand_shortcodes_for_cms("<p>[page 3]</p>", "de") == (
        f'<p><a href="{UBER_DIE_APP_URL}" data-integreat-auto-update="true">'
        "Über die App Integreat Augsburg</a></p>"
    )


@pytest.mark.django_db
def test_collapse_auto_updating_link(load_test_data: None) -> None:
    """
    An auto updating link collapses to a ``[page]`` shortcode without link text
    """
    assert (
        collapse(
            f'<p><a href="{WILLKOMMEN_URL}" data-integreat-auto-update="true">Willkommen</a></p>'
        )
        == "<p>[page 1]</p>"
    )


@pytest.mark.django_db
def test_collapse_link_with_custom_text(load_test_data: None) -> None:
    """
    A link with custom text collapses to a ``[page]`` shortcode with link text
    """
    assert (
        collapse(f'<p>vor <a href="{WILLKOMMEN_URL}">hier</a> nach</p>')
        == '<p>vor [page 1 "hier"] nach</p>'
    )


@pytest.mark.django_db
def test_collapse_link_with_markup(load_test_data: None) -> None:
    """
    A link containing markup collapses to the ``[page_link]`` block shortcode,
    which preserves the inner html
    """
    assert (
        collapse(f'<p><a href="{WILLKOMMEN_URL}"><b>fett</b>e Schrift</a></p>')
        == "<p>[page_link 1]<b>fett</b>e Schrift[/page_link]</p>"
    )


@pytest.mark.django_db
def test_collapse_link_with_quote_in_text(load_test_data: None) -> None:
    """
    Link texts which cannot be expressed as a shortcode argument
    fall back to the ``[page_link]`` block shortcode
    """
    assert (
        collapse(f'<p><a href="{WILLKOMMEN_URL}">"hier"</a></p>')
        == '<p>[page_link 1]"hier"[/page_link]</p>'
    )


@pytest.mark.django_db
def test_collapse_short_url(load_test_data: None) -> None:
    """
    Short urls to pages are collapsed as well
    """
    assert (
        collapse('<p><a href="http://localhost:8000/s/p/1/">hier</a></p>')
        == '<p>[page 1 "hier"]</p>'
    )


@pytest.mark.django_db
def test_collapse_leaves_external_links_alone(load_test_data: None) -> None:
    """
    Only links to pages are collapsed
    """
    content = '<p><a href="https://example.com/">extern</a></p>'
    assert collapse(content) == content


@pytest.mark.django_db
def test_collapse_leaves_other_internal_links_alone(load_test_data: None) -> None:
    """
    Links to events, locations and the imprint are not collapsed yet
    """
    content = (
        '<p><a href="https://integreat.app/augsburg/de/events/test-veranstaltung/">'
        "Veranstaltung</a></p>"
    )
    assert collapse(content) == content


@pytest.mark.django_db
def test_collapse_link_to_draft_page(load_test_data: None) -> None:
    """
    Links to pages without a public translation are collapsed too,
    so that they do not end up in the link index either
    """
    unpublish_page_3()
    assert (
        collapse(f'<p><a href="{UBER_DIE_APP_URL}">hier</a></p>')
        == '<p>[page 3 "hier"]</p>'
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "shortcodes",
    [
        "<p>[page 1]</p>",
        '<p>[page 1 "hier"]</p>',
        "<p>[page_link 1]<b>fett</b>[/page_link]</p>",
        '<p>vor [page 1] mitte [page 1 "da"] nach</p>',
        "<ul><li>[page 1]</li><li>[page 3]</li></ul>",
    ],
)
def test_round_trip(load_test_data: None, shortcodes: str) -> None:
    """
    Expanding and collapsing again must not change the stored content
    """
    assert collapse(expand_shortcodes_for_cms(shortcodes, "de")) == shortcodes


@pytest.mark.django_db
def test_clean_content_collapses_internal_links(load_test_data: None) -> None:
    """
    Content saved through :func:`~integreat_cms.cms.utils.content_utils.clean_content`
    must never contain urls to internal pages
    """
    cleaned = clean_content(
        f'<p><a href="{WILLKOMMEN_URL}">hier</a> und '
        '<a href="https://example.com/">extern</a></p>',
        "de",
        1,
    )
    assert WILLKOMMEN_URL not in cleaned
    assert '[page 1 "hier"]' in cleaned
    assert 'href="https://example.com/"' in cleaned


@pytest.mark.django_db
def test_collapse_link_with_ampersand_in_text(load_test_data: None) -> None:
    """
    Link texts containing characters which are html escaped when the content is serialized
    also fall back to the block scoped shortcode, so that no second layer of escaping
    piles up on every save
    """
    assert (
        collapse(f'<p><a href="{WILLKOMMEN_URL}">Recht &amp; Ordnung</a></p>')
        == "<p>[page_link 1]Recht &amp; Ordnung[/page_link]</p>"
    )


@pytest.mark.django_db
def test_collapse_linked_image(load_test_data: None) -> None:
    """
    A linked image keeps its image element and is wrapped in the block scoped shortcode
    """
    assert (
        collapse(
            f'<p><a href="{WILLKOMMEN_URL}" aria-hidden="true" tabindex="-1">'
            '<img src="/media/test.png" alt=""></a></p>'
        )
        == '<p>[page_link 1]<img src="/media/test.png" alt="">[/page_link]</p>'
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "shortcodes",
    [
        "<p>[page_link 1]Recht &amp; Ordnung[/page_link]</p>",
        '<p>[page_link 1]<img src="/media/test.png" alt="">[/page_link]</p>',
    ],
)
def test_round_trip_of_escaped_content(
    load_test_data: None,
    shortcodes: str,
) -> None:
    """
    Content which needs html escaping must survive an arbitrary number of save cycles
    """
    content = shortcodes
    for _iteration in range(3):
        content = collapse(expand_shortcodes_for_cms(content, "de"))
        assert content == shortcodes


@pytest.mark.django_db
def test_content_form_expands_shortcodes_for_the_editor(load_test_data: None) -> None:
    """
    The content which is put into the editor contains links instead of shortcodes
    """
    from integreat_cms.cms.forms import PageTranslationForm

    translation = get_latest_german_translation(page_id=2)
    PageTranslation.objects.filter(pk=translation.pk).update(
        content='<p>[page 1 "hier"]</p>',
    )
    translation.refresh_from_db()

    form = PageTranslationForm(instance=translation)
    assert form.initial["content"] == f'<p><a href="{WILLKOMMEN_URL}">hier</a></p>'


@pytest.mark.django_db
def test_content_form_collapses_links_on_save(load_test_data: None) -> None:
    """
    What the editor submits is stored as shortcodes, so that no url to internal content
    is ever handed to ``linkcheck``
    """
    from integreat_cms.cms.forms import PageTranslationForm

    translation = get_latest_german_translation(page_id=2)
    form = PageTranslationForm(
        data={
            "title": translation.title,
            "slug": translation.slug,
            "status": translation.status,
            "content": f'<p><a href="{WILLKOMMEN_URL}">hier</a></p>',
        },
        instance=translation,
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["content"] == '<p>[page 1 "hier"]</p>'
    assert "integreat.app" not in form.cleaned_data["content"]


@pytest.mark.django_db
def test_expanded_content_is_not_cached(load_test_data: None) -> None:
    """
    ``content_for_cms`` must follow later changes of the content.

    It must not be a cached property: the content form reads it while initializing and then
    assigns the submitted content to the very same instance, so anything reading it during
    ``pre_save`` (the HIX score calculation does) would otherwise see the previous content.
    """
    translation = get_latest_german_translation(page_id=2)
    translation.content = '<p>[page 1 "hier"]</p>'
    assert translation.content_for_cms == f'<p><a href="{WILLKOMMEN_URL}">hier</a></p>'

    translation.content = "<p>Neuer Inhalt</p>"
    assert translation.content_for_cms == "<p>Neuer Inhalt</p>"


@pytest.mark.django_db
def test_content_form_does_not_freeze_expanded_content(load_test_data: None) -> None:
    """
    After the content form has been validated, the expanded content of its instance must
    reflect what was submitted, not what was in the database when the form was built
    """
    from integreat_cms.cms.forms import PageTranslationForm

    translation = get_latest_german_translation(page_id=2)
    form = PageTranslationForm(
        data={
            "title": translation.title,
            "slug": translation.slug,
            "status": translation.status,
            "content": "<p>Neuer Inhalt</p>",
        },
        instance=translation,
    )
    # Building the form reads the expanded content to populate the editor
    assert form.initial["content"]
    assert form.is_valid(), form.errors

    assert form.instance.content_for_cms == "<p>Neuer Inhalt</p>"


def get_latest_german_translation(page_id: int) -> PageTranslation:
    """
    Get the latest German translation of the given page

    :param page_id: The id of the page
    :return: The translation
    """
    return (
        PageTranslation.objects.filter(page_id=page_id, language__slug="de")
        .order_by("-version")
        .first()
    )
