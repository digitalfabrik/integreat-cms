"""
This module tests that shortcodes are expanded in the content delivered by the API
"""

from __future__ import annotations

import pytest
from django.test.client import Client

from integreat_cms.cms.models import PageTranslation

#: The absolute url of the German translation of page 1 in the Augsburg region
WILLKOMMEN_URL = "https://integreat.app/augsburg/de/willkommen/"


def store_content(content: str, page_id: int = 2) -> None:
    """
    Put the given content into every German translation of a page, bypassing the form so
    that it is stored exactly as given

    :param content: The content to store
    :param page_id: The id of the page whose content should be replaced
    """
    PageTranslation.objects.filter(page_id=page_id, language__slug="de").update(
        content=content,
    )


def get_page(page_id: int = 2) -> dict:
    """
    Request a single page from the API

    :param page_id: The id of the page to request
    :return: The delivered page
    """
    response = Client().get(f"/api/v3/augsburg/de/page/?id={page_id}")
    assert response.status_code == 200, response.content
    return response.json()


@pytest.mark.django_db
def test_page_shortcode_is_delivered_as_absolute_link(load_test_data: None) -> None:
    """
    A page shortcode is delivered as a link with an absolute url.

    Before internal links were stored as shortcodes they were stored as absolute urls, so
    delivering a relative path here would change what clients receive.
    """
    store_content('<p>[page 1 "hier"]</p>')

    assert get_page()["content"] == f'<p><a href="{WILLKOMMEN_URL}">hier</a></p>'


@pytest.mark.django_db
def test_page_shortcode_without_text_is_delivered_with_the_target_title(
    load_test_data: None,
) -> None:
    """
    A page shortcode without link text follows the title of its target
    """
    store_content("<p>[page 1]</p>")

    assert get_page()["content"] == f'<p><a href="{WILLKOMMEN_URL}">Willkommen</a></p>'


@pytest.mark.django_db
def test_page_link_shortcode_is_delivered_as_absolute_link(
    load_test_data: None,
) -> None:
    """
    The block scoped shortcode wraps its content in a link with an absolute url too
    """
    store_content("<p>[page_link 1]<b>hier</b>[/page_link]</p>")

    assert get_page()["content"] == f'<p><a href="{WILLKOMMEN_URL}"><b>hier</b></a></p>'


@pytest.mark.django_db
def test_shortcode_is_stripped_from_the_excerpt(load_test_data: None) -> None:
    """
    The excerpt is derived from the expanded content, so it contains the link text
    instead of the shortcode
    """
    store_content('<p>[page 1 "hier"]</p>')

    assert get_page()["excerpt"] == "hier"


@pytest.mark.django_db
def test_delivered_content_never_contains_a_shortcode(load_test_data: None) -> None:
    """
    Whatever happens, no shortcode may leak into the delivered content
    """
    store_content('<p>[page 1] and [page 1 "hier"]</p>')

    content = get_page()["content"]
    assert "[page" not in content
