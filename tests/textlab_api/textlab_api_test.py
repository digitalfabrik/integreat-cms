from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from django.http import HttpResponse
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.constants.roles import EDITOR
from integreat_cms.cms.models.pages.page import Page
from integreat_cms.cms.models.pages.page_translation import PageTranslation
from integreat_cms.cms.models.regions.region import Region
from tests.mock import MockServer

if TYPE_CHECKING:
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper


def update_page_content(
    admin_client: Client,
    title: str,
    content: str,
    hix_ignore: bool = False,
) -> tuple[str, HttpResponse]:

    edit_page = reverse(
        "edit_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
            "page_id": 2,
        },
    )
    edit_page_data = {
        "title": title,
        "content": content,
        "mirrored_page_region": "",
        "_ref_node_id": 3,
        "_position": "right",
        "status": status.PUBLIC,
    }
    if hix_ignore:
        edit_page_data["hix_ignore"] = "on"

    return (edit_page, admin_client.post(edit_page, edit_page_data))


# This is a faked HIX feedback to be used in the next test
dummy_hix_result = {
    "formulaHix": 15.48920568,
    "moreSentencesInClauses": [1, 2, 3],
    "moreSentencesInWords": [],
    "dataTerms": {
        "1289": {
            "category": {
                "category_type": "negative",
                "description": {
                    "de": "Abkürzungen erschweren den Lesefluss und werden häufig auch nicht verstanden.",
                    "en": "Abbreviations make it harder to read and understand your text.<br>Tip: Try to use abbreviations spraringly. <br>If you need to use lesser known abbreviations, explain them to your readers.",
                },
                "id": 1289,
                "locale_name": "de_DE",
                "name": {
                    "de": "Abkürzungen",
                    "en": "Abbreviations for Cockpit Integreat",
                },
                "settings": {},
            },
            "result": [
                {
                    "length": [1],
                    "position": [136],
                    "priority": 6,
                    "replacement": [
                        {
                            "description": "",
                            "global_visible": 1,
                            "id": 309900,
                            "lemma": ["Jahrhundert"],
                            "settings": {},
                            "tag": ["NN"],
                            "wordcount": 1,
                            "words": ["Jahrhundert"],
                        }
                    ],
                    "term": {
                        "check_words": 1,
                        "description": "Verwenden Sie so wenige Abkürzungen im Text wie möglich.|Nicht alle Abkürzungen sind Ihren Lesern bekannt.",
                        "lemma": ["Jh.{0,1}"],
                        "settings": {"syllcount": 2},
                        "tag": [""],
                        "term_id": 143,
                        "wordcount": 1,
                        "words": ["Jh.{0,1}"],
                    },
                },
                {
                    "length": [1, 1],
                    "position": [353, 355],
                    "priority": 6,
                    "replacement": [
                        {
                            "description": "",
                            "global_visible": 1,
                            "id": 369,
                            "lemma": ["<unknown>", "<unknown>", "<unknown>"],
                            "settings": {},
                            "tag": ["NE", "NE", "NN"],
                            "wordcount": 3,
                            "words": ["Frequently", "Asked", "Questions"],
                        }
                    ],
                    "term": {
                        "check_words": 1,
                        "description": "Verwenden Sie so wenige Abkürzungen im Text wie möglich.|Nicht alle Abkürzungen sind Ihren Lesern bekannt.",
                        "lemma": ["<unknown>"],
                        "settings": {"syllcount": 2},
                        "tag": ["NE"],
                        "term_id": 368,
                        "wordcount": 1,
                        "words": ["FAQ"],
                    },
                },
            ],
        },
    },
}


@pytest.mark.django_db
def test_hix_score_update(
    load_test_data: None,
    admin_client: Client,
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    Check that the HIX score is requested and saved when the page translation is updated

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the dummy http server
    """
    # Setup a mocked Textlab API server with dummy responses
    mock_server.configure("/user/login", 200, {"token": "dummy"})
    mock_server.configure(
        "/benchmark/420",
        200,
        dummy_hix_result,
    )

    # Redirect call aimed at the Textlab API to the fake server
    settings.TEXTLAB_API_URL = f"http://localhost:{mock_server.port}"

    # Enable Textlab in the test region
    Region.objects.filter(slug="augsburg").update(hix_enabled=True)

    edit_page, response = update_page_content(
        admin_client, "Willkommen in Augsburg", "Neuer Inhalt"
    )

    assert response.status_code == 302
    assert response.headers.get("Location") == edit_page

    # Check the updated HIX score
    page_translation = Page.objects.get(id=2).get_translation("de")

    assert page_translation.hix_score == 15.48920568
    assert json.loads(page_translation.hix_feedback) == [
        {"category": "nested-sentences", "result": 3},
        {"category": "long-sentences", "result": 0},
        {"category": "long-words", "result": 0},
        {"category": "passive-voice-sentences", "result": 0},
        {"category": "infinitive-constructions", "result": 0},
        {"category": "nominal-sentences", "result": 0},
        {"category": "future-tense-sentences", "result": 0},
        {"category": "abbreviations", "result": 3},
    ]
    assert mock_server.requests_counter == 2


@pytest.mark.django_db
def test_hix_disable_on_region(
    load_test_data: None,
    admin_client: Client,
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    Check that the HIX score is not updated when hix is disabled on region level. No request to TextLab API is expected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the dummy http server
    """

    # Setup a mocked Textlab API server with dummy responses
    mock_server.configure("/user/login", 200, {"token": "dummy"})
    mock_server.configure("/benchmark/420", 200, {"formulaHix": 20.0})

    # Redirect call aimed at the Textlab API to the fake server
    settings.TEXTLAB_API_URL = f"http://localhost:{mock_server.port}"

    # Disable Textlab in the test region
    Region.objects.filter(slug="augsburg").update(hix_enabled=False)

    edit_page, response = update_page_content(
        admin_client, "Willkommen in Augsburg", "Neuer Inhalt1"
    )

    assert response.status_code == 302
    assert response.headers.get("Location") == edit_page

    # Check that HIX score was not updated
    page_translation = Page.objects.get(id=2).get_translation("de")

    assert page_translation.hix_score is None
    assert page_translation.hix_feedback is None
    assert mock_server.requests_counter == 0


@pytest.mark.django_db
def test_ignore_hix_on_page(
    load_test_data: None,
    admin_client: Client,
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    Check that the HIX score is not updated when hix is disabled at the page level (hix_ignore=True). No request to TextLab API is expected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the dummy http server
    """

    # Setup a mocked Textlab API server with dummy responses
    mock_server.configure("/user/login", 200, {"token": "dummy"})
    mock_server.configure("/benchmark/420", 200, {"formulaHix": 20.0})

    # Redirect call aimed at the Textlab API to the fake server
    settings.TEXTLAB_API_URL = f"http://localhost:{mock_server.port}"

    # Enable Textlab in the test region
    Region.objects.filter(slug="augsburg").update(hix_enabled=True)

    edit_page, response = update_page_content(
        admin_client, "Willkommen in Augsburg", "Neuer Inhalt2", hix_ignore=True
    )

    assert response.status_code == 302
    assert response.headers.get("Location") == edit_page

    # Check that the HIX score has not been updated
    page_translation = Page.objects.get(id=2).get_translation("de")

    assert page_translation.hix_score is None
    assert page_translation.hix_feedback is None
    assert mock_server.requests_counter == 0


@pytest.mark.django_db
def test_hix_page_content_empty(
    load_test_data: None,
    admin_client: Client,
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    Check that the HIX score is not updated when hix is enabled on page level and page content is empty. No request to TextLab API is expected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the dummy http server
    """

    # Setup a mocked Textlab API server with dummy responses
    mock_server.configure("/user/login", 200, {"token": "dummy"})
    mock_server.configure("/benchmark/420", 200, {"formulaHix": 20.0})

    # Redirect call aimed at the Textlab API to the fake server
    settings.TEXTLAB_API_URL = f"http://localhost:{mock_server.port}"

    # Enable Textlab in the test region
    Region.objects.filter(slug="augsburg").update(hix_enabled=True)

    edit_page, response = update_page_content(
        admin_client, "Willkommen in Augsburg", ""
    )

    assert response.status_code == 302
    assert response.headers.get("Location") == edit_page

    # Check that the HIX score has not been updated
    page_translation = Page.objects.get(id=2).get_translation("de")

    assert page_translation.hix_score is None
    assert page_translation.hix_feedback is None
    assert mock_server.requests_counter == 0


@pytest.mark.django_db
def test_hix_no_content_changes(
    load_test_data: None,
    admin_client: Client,
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    Check that the HIX score is copied from the previous translation version if the page content is not changed. No request to TextLab API is expected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the dummy http server
    """

    # Setup a mocked Textlab API server with dummy responses
    mock_server.configure("/user/login", 200, {"token": "dummy"})
    mock_server.configure("/benchmark/420", 200, {"formulaHix": 20.0})

    # Redirect call aimed at the Textlab API to the fake server
    settings.TEXTLAB_API_URL = f"http://localhost:{mock_server.port}"

    # Enable Textlab in the test region
    Region.objects.filter(slug="augsburg").update(hix_enabled=True)

    # Save data from the previous version of the translation
    previous_translation = Page.objects.get(id=2).get_translation("de")

    previous_hix_score = previous_translation.hix_score
    previous_hix_feedback = previous_translation.hix_feedback

    previous_content = previous_translation.content
    assert previous_content != ""

    edit_page, response = update_page_content(
        admin_client, "Neuer Titel", previous_content
    )

    assert response.status_code == 302
    assert response.headers.get("Location") == edit_page

    # Check that the HIX score has been copied from the previous version
    page_translation = Page.objects.get(id=2).get_translation("de")

    assert page_translation.hix_score == previous_hix_score
    assert json.loads(page_translation.hix_feedback) == json.loads(
        previous_hix_feedback
    )
    assert mock_server.requests_counter == 0


@pytest.mark.django_db
def test_hix_response_400(
    load_test_data: None,
    admin_client: Client,
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    Check that the HIX score is not being updated when the API returns a HTTP 400 error.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the dummy http server
    """
    # Setup a mocked Textlab API server with dummy responses
    mock_server.configure("/user/login", 200, {"token": "dummy"})
    mock_server.configure("/benchmark/420", 400, {"message": "Error occurred"})

    # Redirect call aimed at the Textlab API to the fake server
    settings.TEXTLAB_API_URL = f"http://localhost:{mock_server.port}"

    # Enable Textlab in the test region
    Region.objects.filter(slug="augsburg").update(hix_enabled=True)

    edit_page, response = update_page_content(
        admin_client, "Willkommen in Augsburg", "Neuer Inhalt3"
    )

    assert response.status_code == 302
    assert response.headers.get("Location") == edit_page

    # Check that the HIX score has not been updated
    page_translation = Page.objects.get(id=2).get_translation("de")

    assert page_translation.hix_score is None
    assert page_translation.hix_feedback is None
