from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Final

    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

    from tests.mock import MockServer

import pytest
from django.apps import apps
from django.urls import reverse

from integreat_cms.cms.models import Page
from tests.constants import (
    AUTHOR,
    EDITOR,
    MANAGEMENT,
    PRIV_STAFF_ROLES,
)

from .utils import get_content_translations

# Slugs we want to use for testing
REGION_SLUG: Final[str] = "augsburg"
SOURCE_LANGUAGE_SLUG: Final[str] = "de"
TARGET_LANGUAGE_SLUG: Final[str] = "en"


def setup_fake_deepl_api_server(mock_server: MockServer) -> None:
    """
    Setup a mocked DeepL API server with dummy response

    :param mock_server: The fixture providing the mock http server for faking the DeepL API server
    """
    mock_server.configure(
        "/v2/translate",
        200,
        {
            "translations": [
                {
                    "detected_source_language": "DE",
                    "text": "This is your translation from DeepL",
                    "billed_characters": 0,
                },
            ],
        },
    )


def setup_deepl_supported_languages(
    source_languages: list[str],
    target_languages: list[str],
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
    "login_role_user",
    [*PRIV_STAFF_ROLES, AUTHOR, MANAGEMENT, EDITOR],
    indirect=True,
)
@pytest.mark.parametrize("error", api_errors)
def test_deepl_bulk_mt_api_error(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    error: int,
    settings: SettingsWrapper,
    mock_server: MockServer,
    django_capture_on_commit_callbacks: Any,
) -> None:
    """
    Check for error handling when DeepL API returns server error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param error: The error status to test
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    mock_server.configure("/v2/translate", error, {"error": "Error occured"})

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"

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
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            machine_translation, data={"selected_ids[]": selected_ids}
        )
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
        Page,
        selected_ids,
        TARGET_LANGUAGE_SLUG,
    )

    # Translation now happens via a Celery task (eager in tests), so the
    # failure surfaces through the queued report rather than a synchronous
    # Django message - see the outcome bug fixed in machine_translation_report.py,
    # which this also guards against regressing.
    report_url = reverse(
        "machine_translation_report",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
            "model_type": "page",
        },
    )
    report_response = client.get(report_url)
    report_data = report_response.json()
    assert report_data["reports"], "Expected a queued machine translation report"
    assert report_data["reports"][-1]["outcome"] == "PARTIAL_SUCCESS"

    for page_translation in page_translations:
        # Check that the page was not machine translated
        assert (
            page_translation[TARGET_LANGUAGE_SLUG] is None
            or page_translation[TARGET_LANGUAGE_SLUG].machine_translated is False
        )
