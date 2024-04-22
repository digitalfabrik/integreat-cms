from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import pytest
from django.http import HttpResponse
from django.test.client import Client
from django.urls import reverse
from werkzeug.wrappers import Request, Response

from integreat_cms.cms.constants import status
from integreat_cms.cms.constants.roles import EDITOR
from integreat_cms.cms.models.pages.page import Page
from integreat_cms.cms.models.pages.page_translation import PageTranslation
from integreat_cms.cms.models.regions.region import Region
from tests.mock import MockServer

if TYPE_CHECKING:
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper
    from pytest_httpserver.httpserver import HTTPServer


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
    mock_server.configure("/benchmark/420", 200, {"formulaHix": 15.48920568})

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
    mock_server.configure("/benchmark/420", 200, {"message": "Error occurred"})

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
    mock_server.configure("/benchmark/420", 500, {"message": "Error occurred"})

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
    mock_server.configure("/benchmark/420", 500, {"message": "Error occurred"})

    # Redirect call aimed at the Textlab API to the fake server
    settings.TEXTLAB_API_URL = f"http://localhost:{mock_server.port}"

    # Enable Textlab in the test region
    Region.objects.filter(slug="augsburg").update(hix_enabled=True)

    # Setting HIX score initial value
    initial_hix_score = 11
    PageTranslation.objects.filter(page__id=2, language__slug="de").update(
        hix_score=initial_hix_score
    )

    # Check initial page properties
    page_translation = Page.objects.get(id=2).get_translation("de")
    content_before_change = page_translation.content
    assert content_before_change != ""
    assert page_translation.latest_version.hix_score == initial_hix_score

    edit_page, response = update_page_content(
        admin_client, "Neuer Titel", content_before_change
    )

    assert response.status_code == 302
    assert response.headers.get("Location") == edit_page

    # Check that the HIX score has been copied from the previous version
    page_translation = Page.objects.get(id=2).get_translation("de")

    assert page_translation.hix_score == initial_hix_score
    assert page_translation.content == content_before_change
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
