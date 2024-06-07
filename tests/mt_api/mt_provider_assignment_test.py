from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final
    from pytest_django.fixtures import SettingsWrapper
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client

import pytest
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import Language, LanguageTreeNode, Region

from ..conftest import ANONYMOUS, HIGH_PRIV_STAFF_ROLES, MANAGEMENT
from .deepl_api_test import setup_deepl_supported_languages
from .google_translate_api_test import setup_google_translate_supported_languages

# Slugs we want to use for testing
REGION_SLUG: Final[str] = "augsburg"


def check_mt_provider(
    region_slug: str, language_slug: str, mt_provider: str | None
) -> None:
    """
    Check whether the correct MT provider is assigned for the language

    :param region_slug: slug of the region used in the test
    :param language_slug: Language whose MT provider must be checked
    :param mt_provider: MT provider which should be assigned for the language in the region
    """

    region = Region.objects.filter(slug=region_slug).first()
    language = Language.objects.filter(slug=language_slug).first()
    language_node = LanguageTreeNode.objects.filter(
        region=region, language=language
    ).first()

    if mt_provider:
        assert language_node.mt_provider.name == mt_provider
    else:
        assert not language_node.mt_provider


@pytest.mark.django_db
def test_no_available_provider(
    load_test_data: None,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check the provider assignment for the case no MT provider supports any language

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param caplog: The :fixture:`caplog` fixture
    """

    # Set up so that neither DeepL nor Google Translate support any language
    setup_deepl_supported_languages([], [])
    setup_google_translate_supported_languages([], [])

    # Check no MT provider is assigned
    check_mt_provider(REGION_SLUG, "en", None)
    check_mt_provider(REGION_SLUG, "ar", None)
    check_mt_provider(REGION_SLUG, "hidden", None)


@pytest.mark.django_db
def test_only_deepl_available(
    load_test_data: None,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check the provider assignment for the case when only DeepL is supporting some languages but not all

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param caplog: The :fixture:`caplog` fixture
    """

    # Set up so only the combination of English and DeepL works
    setup_deepl_supported_languages(["de"], ["en"])
    setup_google_translate_supported_languages([], [])

    # Check only English by DeepL is allowed
    check_mt_provider(REGION_SLUG, "en", "DeepL")
    check_mt_provider(REGION_SLUG, "ar", None)
    check_mt_provider(REGION_SLUG, "hidden", None)


@pytest.mark.django_db
def test_only_google_translate_available(
    load_test_data: None,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check the provider assignment for the case when only Google Translate is supporting some languages but not all

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param caplog: The :fixture:`caplog` fixture
    """

    # Set up so only the combinations of English by Google translate and Arabic by Google Translate work
    setup_deepl_supported_languages([], [])
    setup_google_translate_supported_languages(["de", "en"], ["en", "ar"])

    # Check English and Arabic are available for MT by Google Translate
    check_mt_provider(REGION_SLUG, "en", "Google Translate")
    check_mt_provider(REGION_SLUG, "ar", "Google Translate")
    check_mt_provider(REGION_SLUG, "hidden", None)


@pytest.mark.django_db
def test_both_providers_available(
    load_test_data: None,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check the provider assignment for the case when multiple of MT provider and languages are available for MT

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param caplog: The :fixture:`caplog` fixture
    """

    # Set up so English is supported by both of them but Arabic only by Google
    setup_deepl_supported_languages(["de"], ["en"])
    setup_google_translate_supported_languages(["de", "en"], ["en", "ar"])

    # Check DeepL is assigned for English due to the order
    check_mt_provider(REGION_SLUG, "en", "DeepL")
    # Check Arabic MT is available by Google Translate
    check_mt_provider(REGION_SLUG, "ar", "Google Translate")
    # No supporting provider
    check_mt_provider(REGION_SLUG, "hidden", None)


@pytest.mark.django_db
def test_change_to_supporting_provider(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check the preferred MT provider can be changed correctly

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """

    # Set up so that English is supported by both DeepL and Google Translate
    setup_deepl_supported_languages(["de"], ["en"])
    setup_google_translate_supported_languages(["de"], ["en"])

    # Ensure that English is currently supported by DeepL
    check_mt_provider(REGION_SLUG, "en", "DeepL")

    # Log the user in
    client, role = login_role_user

    # Assign Google Translate for English
    url = reverse("translations_management", kwargs={"region_slug": "augsburg"})
    response = client.post(
        url,
        data={
            "machine_translate_pages": 1,
            "machine_translate_events": 1,
            "machine_translate_pois": 1,
            "en": ["Google Translate"],
            "ar": ["Google Translate"],
            "fa": ["Google Translate"],
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES + [MANAGEMENT]:
        assert response.status_code == 302
        # Check the provider assignment was successfully changed
        check_mt_provider(REGION_SLUG, "en", "Google Translate")
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert response.headers.get("location") == f"{settings.LOGIN_URL}?next={url}"
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_change_to_not_supporting_provider(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check the MT provider assignment fails when a provider is selected which does not support the language

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """
    # Set up so that English is only supported by DeepL
    setup_deepl_supported_languages(["de"], ["en"])
    setup_google_translate_supported_languages(["de"], ["ar"])

    # Ensure that English is currently supported by DeepL
    check_mt_provider(REGION_SLUG, "en", "DeepL")

    # Log the user in
    client, role = login_role_user

    # Assign Google Translate for English
    url = reverse("translations_management", kwargs={"region_slug": "augsburg"})
    response = client.post(
        url,
        data={
            "machine_translate_pages": 1,
            "machine_translate_events": 1,
            "machine_translate_pois": 1,
            "en": ["Google Translate"],
            "ar": ["Google Translate"],
            "fa": ["Google Translate"],
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES + [MANAGEMENT]:
        assert response.status_code == 302
        # Check the provider assignment was not changed
        check_mt_provider(REGION_SLUG, "en", "DeepL")
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert response.headers.get("location") == f"{settings.LOGIN_URL}?next={url}"
    else:
        assert response.status_code == 403
