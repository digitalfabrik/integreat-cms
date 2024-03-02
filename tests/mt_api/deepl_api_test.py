from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Final
    from pytest_django.fixtures import SettingsWrapper
    from django.db.models.base import ModelBase
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_httpserver.httpserver import HTTPServer

import pytest
from django.apps import apps
from django.urls import reverse

from integreat_cms.cms.models import Page

from ..conftest import AUTHOR, EDITOR, MANAGEMENT, PRIV_STAFF_ROLES
from ..utils import assert_message_in_log
from .utils import get_content_translations

# Slugs we want to use for testing
REGION_SLUG: Final[str] = "augsburg"
SOURCE_LANGUAGE_SLUG: Final[str] = "de"
TARGET_LANGUAGE_SLUG: Final[str] = "en"


def setup_fake_deepl_api_server(httpserver: HTTPServer) -> None:
    """
    Setup a mocked DeepL API server with dummy response

    :param httpserver: The fixture providing the dummy http server used for faking the DeepL API server
    """
    httpserver.expect_request("/v2/translate").respond_with_json(
        {
            "translations": [
                {
                    "detected_source_language": "DE",
                    "text": "This is your translation from DeepL",
                }
            ]
        }
    )


def setup_deepl_supported_languages(
    source_languages: list[str], target_languages: list[str]
) -> None:
    """
    Setup supported languages for DeepL

    :param source_languages: The supported source languages
    :param target_languages: The supported target languages
    """
    apps.get_app_config("deepl_api").supported_source_languages = source_languages
    apps.get_app_config("deepl_api").supported_target_languages = target_languages


# Possible errors from DeepL API
api_errors = [404, 413, 429, 456, 500]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.parametrize("error", api_errors)
def test_deepl_bulk_mt_api_error(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    error: int,
    settings: SettingsWrapper,
    httpserver: HTTPServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for error handling when DeepL API returns server error
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param error: The error status to test
    :param settings: The fixture providing the django settings
    :param httpserver: The fixture providing the dummy http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    httpserver.expect_request("/v2/translate").respond_with_data("Error", status=error)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{httpserver.port}"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    selected_ids = [1, 2, 3]
    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    response = client.post(machine_translation, data={"selected_ids[]": selected_ids})
    print(response.headers)

    assert response.status_code == 302
    page_tree = reverse(
        "pages",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    assert response.headers.get("Location") == page_tree
    response = client.get(page_tree)

    # Get the page objects including their translations from the database
    page_translations = get_content_translations(
        Page, selected_ids, TARGET_LANGUAGE_SLUG
    )

    for page_translation in page_translations:
        # Check for a failure message
        assert_message_in_log(
            "ERROR    A problem with DeepL API has occurred. Please contact an administrator.",
            caplog,
        )
        # Check that the page was not machine translated
        assert (
            page_translation[TARGET_LANGUAGE_SLUG] is None
            or page_translation[TARGET_LANGUAGE_SLUG].machine_translated is False
        )
