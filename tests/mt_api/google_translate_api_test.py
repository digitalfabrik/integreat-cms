from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final
    from pytest_django.fixtures import SettingsWrapper
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client

import pytest
from django.apps import apps
from django.urls import reverse

from ..conftest import AUTHOR, EDITOR, MANAGEMENT, PRIV_STAFF_ROLES
from ..utils import assert_message_in_log

if TYPE_CHECKING:
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

# Slugs we want to use for testing
REGION_SLUG: Final[str] = "augsburg"
SOURCE_LANGUAGE_SLUG: Final[str] = "en"
TARGET_LANGUAGE_SLUG: Final[str] = "ar"


def setup_google_translate_supported_languages(
    source_languages: list[str], target_languages: list[str]
) -> None:
    """
    Setup supported languages for Google Translate

    :param source_languages: The supported source languages
    :param target_languages: The supported target languages
    """
    apps.get_app_config("google_translate_api").supported_source_languages = (
        source_languages
    )
    apps.get_app_config("google_translate_api").supported_target_languages = (
        target_languages
    )


# pylint:disable=too-few-public-methods
class FakeClient:
    """
    Fake client to replace translate_v2.Client
    """

    def translate(
        self,
        values: list[str],
        target_language: str,
        source_language: str,
        format_: str,
    ) -> list:
        return [{"translatedText": "This is your translation from Google Translate"}]


def setup_fake_google_translate_api(  # type: ignore[no-untyped-def]
    self, request: HttpRequest, form_class: ModelFormMetaclass
) -> None:
    """
    Setup a fake for Google Translate API

    :param request: The current request
    :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                       subclass of the current content type
    """

    self.request = request
    self.region = request.region
    self.form_class = form_class
    self.translatable_attributes = ["title", "content", "meta_description"]

    self.translator_v2 = FakeClient()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
def test_google_translate_error(
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for error handling

    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup supported languages
    setup_google_translate_supported_languages(["en"], ["ar"])

    # Log the user in
    client, _role = login_role_user

    # Try MT translation without patch
    selected_ids = [19]
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

    assert_message_in_log(
        "ERROR    A problem with Google Translate API has occurred. Please contact an administrator.",
        caplog,
    )
