from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Final
    from pytest_django.fixtures import SettingsWrapper
    from django.db.models.base import ModelBase
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client

from unittest.mock import patch

import pytest
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Event, Language, Page, POI, Region
from integreat_cms.cms.models.pois.poi import get_default_opening_hours
from integreat_cms.cms.utils.stringify_list import iter_to_string
from integreat_cms.google_translate_api.google_translate_api_client import (
    GoogleTranslateApiClient,
)
from tests.mock import MockServer

from ..conftest import (
    ANONYMOUS,
    AUTHOR,
    EDITOR,
    MANAGEMENT,
    PRIV_STAFF_ROLES,
    WRITE_ROLES,
)
from ..utils import assert_message_in_log
from .deepl_api_test import setup_deepl_supported_languages, setup_fake_deepl_api_server
from .google_translate_api_test import (
    setup_fake_google_translate_api,
    setup_google_translate_supported_languages,
)
from .utils import get_content_translations, get_english_name, get_word_count

# Slugs we want to use for testing
REGION_SLUG: Final[str] = "augsburg"
# (<MT provider>, <source language>, <target language>)
provider_language_combination = [
    ("DeepL", "de", "en"),
    ("Google Translate", "en", "ar"),
]


def mt_setup(
    deepl_source: list[str],
    deepl_target: list[str],
    gt_source: list[str],
    gt_target: list[str],
    settings: SettingsWrapper,
    mock_server: MockServer | None,
) -> None:
    """
    Function to set up the user language and MT providers

    :param deepl_source: available source languages of DeepL
    :param deepl_target: available target languages of DeepL
    :param gt_source: available source languages of Google Translate
    :param gt_target: available target languages of Google Translate
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    """

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Set up MT API supported languages
    setup_deepl_supported_languages(deepl_source, deepl_target)
    setup_google_translate_supported_languages(gt_source, gt_target)

    if mock_server:
        # Setup a mocked DeepL API server with dummy response
        setup_fake_deepl_api_server(mock_server)
        # Redirect call aimed at the DeepL API to the fake server
        settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"


# Fixture for MT bulk action test
content_role_id_combination = [
    (
        Page,
        PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR],
        [28],
    ),
    (
        POI,
        PRIV_STAFF_ROLES + WRITE_ROLES,
        [6],
    ),
    (
        Event,
        PRIV_STAFF_ROLES + WRITE_ROLES,
        [1],
    ),
]


# pylint:disable=too-many-locals, redefined-outer-name
@pytest.mark.django_db
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
@pytest.mark.parametrize("content_role_id_combination", content_role_id_combination)
def test_bulk_mt(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    content_role_id_combination: tuple[Any, list, list[int]],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation of pages/events/pois via the MT API

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param content_role_id_combination: The combination of content type, user roles with permission and selected_ids used in the test
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    content_type, entitled_roles, ids = content_role_id_combination

    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, mock_server)

    # Log the user in
    client, role = login_role_user
    # Translate the pois
    machine_translation = reverse(
        "machine_translation_" + content_type._meta.default_related_name,
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
        },
    )

    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(machine_translation, data={"selected_ids[]": ids})
        print(response.headers)

        if role in entitled_roles:
            # If the role should be allowed to access the view, we expect a successful result
            assert response.status_code == 302
            tree = reverse(
                content_type._meta.default_related_name,
                kwargs={
                    "region_slug": REGION_SLUG,
                    "language_slug": target_language_slug,
                },
            )
            assert response.headers.get("Location") == tree
            response = client.get(tree)

            translations = get_content_translations(
                content_type, ids, source_language_slug, target_language_slug
            )

            for translation in translations:
                assert_message_in_log(
                    f'SUCCESS  {content_type._meta.verbose_name.capitalize()} "{translation[source_language_slug]}" has successfully been translated ({get_english_name(source_language_slug)} ➜ {get_english_name(target_language_slug)}).',
                    caplog,
                )
                # Check that the page translation exists and really has the correct content
                assert translation[target_language_slug].machine_translated is True
                assert (
                    translation[target_language_slug].title
                    == f"This is your translation from {provider}"
                )
                assert (
                    translation[target_language_slug].content
                    == f"<p>This is your translation from {provider}</p>"
                )
                if (
                    content_type == POI
                    and translation[target_language_slug].meta_description
                ):
                    assert (
                        translation[target_language_slug].meta_description
                        == f"This is your translation from {provider}"
                    )

            # Check that used MT budget value in the region has been increased to the number of translated words
            translated_word_count = get_word_count(
                [translation[source_language_slug] for translation in translations]
            )
            assert (
                Region.objects.get(slug=REGION_SLUG).mt_budget_used
                == translated_word_count
            )

        elif role == ANONYMOUS:
            # For anonymous users, we want to redirect to the login form instead of showing an error
            assert response.status_code == 302
            assert (
                response.headers.get("location")
                == f"{settings.LOGIN_URL}?next={machine_translation}"
            )
        else:
            # For logged in users, we want to show an error if they get a permission denied
            assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_bulk_mt_exceeds_limit(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation error when the attempted translation would exceed the region's word limit

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, None)

    # Setup available translation credits to 0
    settings.MT_CREDITS_FREE = 0

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    selected_ids = [2, 3, 6] if provider == "DeepL" else [18, 19]
    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
        },
    )

    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            machine_translation, data={"selected_ids[]": selected_ids}
        )
        print(response.headers)

        assert response.status_code == 302
        page_tree = reverse(
            "pages",
            kwargs={
                "region_slug": REGION_SLUG,
                "language_slug": target_language_slug,
            },
        )
        assert response.headers.get("Location") == page_tree
        response = client.get(page_tree)

        # Get the page objects including their translations from the database
        page_translations = get_content_translations(
            Page, selected_ids, source_language_slug, target_language_slug
        )

        # Check for a failure message
        translations_str = iter_to_string(
            [t[source_language_slug].title for t in page_translations]
        )
        assert_message_in_log(
            f"ERROR    The following pages could not be translated because they would exceed the remaining budget of 0 words: {translations_str}",
            caplog,
        )
        for page_translation in page_translations:
            assert (
                page_translation[target_language_slug] is None
                or page_translation[target_language_slug].machine_translated is False
            )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_bulk_mt_up_to_date(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation error when one of the target translations is up-to-date and the other is machine translated

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """

    _, _, target_language_slug = provider_language_combination

    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, None)

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    up_to_date_page_id = 1
    machine_translated_page_id = 16

    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
        },
    )

    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            machine_translation,
            data={"selected_ids[]": [up_to_date_page_id, machine_translated_page_id]},
        )
        print(response.headers)

        assert response.status_code == 302
        page_tree = reverse(
            "pages",
            kwargs={
                "region_slug": REGION_SLUG,
                "language_slug": target_language_slug,
            },
        )
        assert response.headers.get("Location") == page_tree
        response = client.get(page_tree)

        # Check for a failure message
        assert_message_in_log(
            "ERROR    All the selected translations are already up-to-date.",
            caplog,
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_bulk_mt_up_to_date_and_ready_for_mt(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation when one of the target translations is up-to-date and the other is ready for MT

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """

    _, source_language_slug, target_language_slug = provider_language_combination

    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, mock_server)

    # Log the user in
    client, _role = login_role_user

    # Translate the pois
    up_to_date_poi_id = 4
    ready_for_mt_poi_id = 6

    machine_translation = reverse(
        "machine_translation_pois",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
        },
    )

    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            machine_translation,
            data={"selected_ids[]": [up_to_date_poi_id, ready_for_mt_poi_id]},
        )
        print(response.headers)

        assert response.status_code == 302
        poi_tree = reverse(
            "pois",
            kwargs={
                "region_slug": REGION_SLUG,
                "language_slug": target_language_slug,
            },
        )
        assert response.headers.get("Location") == poi_tree
        response = client.get(poi_tree)

        poi_translations = get_content_translations(
            POI,
            [up_to_date_poi_id, ready_for_mt_poi_id],
            source_language_slug,
            target_language_slug,
        )

        for poi_translation in poi_translations:
            # Check for a failure message if translation was already up-to-date
            if poi_translation[source_language_slug].poi_id == up_to_date_poi_id:
                assert_message_in_log(
                    f'ERROR    There already is an up-to-date translation for "{poi_translation[settings.LANGUAGE_CODE].title}"',
                    caplog,
                )
                assert poi_translation[target_language_slug].machine_translated is False

            # Check for a successful message if translation was ready for mt
            if poi_translation[source_language_slug].poi_id == ready_for_mt_poi_id:
                assert_message_in_log(
                    f'SUCCESS  Location "{poi_translation[source_language_slug]}" has successfully been translated ({get_english_name(source_language_slug)} ➜ {get_english_name(target_language_slug)}).',
                    caplog,
                )
                assert poi_translation[target_language_slug].machine_translated is True


# Fixture for form translation test
content_role_id_data_combination = [
    (
        Page,
        PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR],
        4,
        {
            "title": "Neuer Titel",
            "content": "Neuer Inhalt",
            "mirrored_page_region": "",
            "_ref_node_id": 3,
            "_position": "right",
            "automatic_translation": "on",
        },
    ),
    (
        POI,
        PRIV_STAFF_ROLES + WRITE_ROLES,
        4,
        {
            "title": "Neuer Titel",
            "content": "Neuer Inhalt",
            "automatic_translation": "on",
            "address": "Test-Straße 5",
            "postcode": "54321",
            "city": "Augsburg",
            "country": "Deutschland",
            "longitude": 1,
            "latitude": 1,
            "opening_hours": json.dumps(get_default_opening_hours()),
            "category": 1,
        },
    ),
    (
        Event,
        PRIV_STAFF_ROLES + WRITE_ROLES,
        1,
        {
            "title": "Neuer Titel",
            "content": "Neuer Inhalt",
            "automatic_translation": "on",
            "start_date": "2030-01-01",
            "end_date": "2030-01-01",
            "is_all_day": True,
        },
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
@pytest.mark.parametrize(
    "content_role_id_data_combination", content_role_id_data_combination
)
def test_automatic_translation(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    content_role_id_data_combination: tuple[Any, list, int, dict],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check machine translation of the page/event/poi when automatic_translation checkbox in set on the form

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param content_role_id_data_combination: The combination of content type, user roles with permission and selected_ids used in the test
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    content_type, entitled_roles, content_id, data = content_role_id_data_combination

    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, mock_server)

    # Log the user in
    client, role = login_role_user

    # Get "page" from PAGE, "poi" from POI and "event" from EVENT
    content_name = content_type._meta.verbose_name if content_type is not POI else "poi"

    create_or_update = (
        "update"
        if content_type.objects.filter(
            id=content_id, translations__language__slug=target_language_slug
        ).exists()
        else "create"
    )

    edit_content = reverse(
        "edit_" + content_name,
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": source_language_slug,
            content_name + "_id": content_id,
        },
    )
    # Adjust keywords
    data = copy.deepcopy(data)
    data.update(
        {
            "mt_translations_to_"
            + create_or_update: Language.objects.filter(slug=target_language_slug)
            .first()
            .id,
            "status": (
                status.REVIEW
                if content_type is Page and role is AUTHOR
                else status.PUBLIC
            ),
        }
    )

    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            edit_content,
            **{"data": data},  # noqa: PIE804
        )

        if role in entitled_roles:
            # If the role should be allowed to access the view, we expect a successful result
            translations = get_content_translations(
                content_type, [content_id], source_language_slug, target_language_slug
            )
            source_translation = translations[0][source_language_slug]
            target_translation = translations[0][target_language_slug]

            # Check that the success message is present
            assert_message_in_log(
                f'SUCCESS  {content_type._meta.verbose_name.capitalize()} "{source_translation.title}" has successfully been translated ({get_english_name(source_language_slug)} ➜ {get_english_name(target_language_slug)}).',
                caplog,
            )

            # Check that the page translation exists and has the correct content
            assert target_translation.machine_translated is True
            assert (
                target_translation.title == f"This is your translation from {provider}"
            )
            assert (
                target_translation.content
                == f"<p>This is your translation from {provider}</p>"
            )
            # Check that used MT budget value in the region has been increased to the number of translated words
            translated_word_count = get_word_count([source_translation])
            assert (
                Region.objects.get(slug=REGION_SLUG).mt_budget_used
                == translated_word_count
            )
        elif role == ANONYMOUS:
            # For anonymous users, we want to redirect to the login form instead of showing an error
            assert response.status_code == 302
            assert (
                response.headers.get("location")
                == f"{settings.LOGIN_URL}?next={edit_content}"
            )
        else:
            # For logged in users, we want to show an error if they get a permission denied
            assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_bulk_mt_no_source_language(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation error when the source language is not available

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """

    _, _, target_language_slug = provider_language_combination

    mt_setup(["ar"], ["en-gb", "en-us"], ["fa"], ["ar"], settings, None)

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    selected_ids = [1, 2, 3]
    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
        },
    )
    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            machine_translation, data={"selected_ids[]": selected_ids}
        )
        print(response.headers)

        assert response.status_code == 302
        page_tree = reverse(
            "pages",
            kwargs={
                "region_slug": REGION_SLUG,
                "language_slug": target_language_slug,
            },
        )
        assert response.headers.get("Location") == page_tree
        response = client.get(page_tree)

        # Get the page objects including their translations from the database
        page_translations = get_content_translations(
            Page, selected_ids, target_language_slug
        )

        # Check for a failure message
        assert_message_in_log(
            f'ERROR    Machine translations are disabled for language "{get_english_name(target_language_slug)}"',
            caplog,
        )
        for page_translation in page_translations:
            # Check that the page was not machine translated
            assert (
                page_translation[target_language_slug] is None
                or page_translation[target_language_slug].machine_translated is False
            )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_deepl_bulk_mt_no_target_language(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation error when the target language is not available

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """

    _, _, target_language_slug = provider_language_combination

    mt_setup(["de"], ["ar"], ["en"], ["fa"], settings, None)

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    selected_ids = [1, 2, 3]
    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
        },
    )
    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            machine_translation, data={"selected_ids[]": selected_ids}
        )
        print(response.headers)

        assert response.status_code == 302
        page_tree = reverse(
            "pages",
            kwargs={
                "region_slug": REGION_SLUG,
                "language_slug": target_language_slug,
            },
        )
        assert response.headers.get("Location") == page_tree
        response = client.get(page_tree)

        # Get the page objects including their translations from the database
        page_translations = get_content_translations(
            Page, selected_ids, target_language_slug
        )

        # Check for a failure message
        assert_message_in_log(
            f'ERROR    Machine translations are disabled for language "{get_english_name(target_language_slug)}"',
            caplog,
        )
        for page_translation in page_translations:
            # Check that the page was not machine translated
            assert (
                page_translation[target_language_slug] is None
                or page_translation[target_language_slug].machine_translated is False
            )
