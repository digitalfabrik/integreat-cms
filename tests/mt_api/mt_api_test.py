from __future__ import annotations

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
    from pytest_httpserver.httpserver import HTTPServer

from unittest.mock import patch

import pytest
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Event, Page, POI, Region
from integreat_cms.cms.models.pois.poi import get_default_opening_hours
from integreat_cms.cms.utils.stringify_list import iter_to_string
from integreat_cms.google_translate_api.google_translate_api_client import (
    GoogleTranslateApiClient,
)

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

content_id_combination = [
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
@pytest.mark.parametrize("content_id_combination", content_id_combination)
def test_bulk_mt(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    content_id_combination: tuple[Any, list, list[int]],
    settings: SettingsWrapper,
    httpserver: HTTPServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation of pois via the MT API

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param content_id_combination: The combination of content type, user roles with permission and selected_ids used in the test
    :param settings: The fixture providing the django settings
    :param httpserver: The fixture providing the dummy http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    content_type, entitled_roles, ids = content_id_combination

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(httpserver)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{httpserver.port}"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])
    setup_google_translate_supported_languages(["en"], ["ar"])

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

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])
    setup_google_translate_supported_languages(["en"], ["ar"])

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

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])
    setup_google_translate_supported_languages(["en"], ["ar"])

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
    httpserver: HTTPServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation when one of the target translations is up-to-date and the other is ready for MT

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param httpserver: The fixture providing the dummy http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """

    _, source_language_slug, target_language_slug = provider_language_combination

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(httpserver)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{httpserver.port}"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])
    setup_google_translate_supported_languages(["en"], ["ar"])

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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_page_automatic_translation(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    httpserver: HTTPServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check machine translation of the page when automatic_translation checkbox in set on the page form

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param httpserver: The fixture providing the dummy http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(httpserver)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{httpserver.port}"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])
    setup_google_translate_supported_languages(["en"], ["ar"])

    # Log the user in
    client, _role = login_role_user

    edit_page = reverse(
        "edit_page",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": source_language_slug,
            "page_id": 2,
        },
    )

    post_data = {
        "title": "Neuer Titel",
        "content": "Neuer Inhalt",
        "mirrored_page_region": "",
        "_ref_node_id": 3,
        "_position": "right",
        "status": status.PUBLIC,
        "automatic_translation": "on",
        "mt_translations_to_create": 2 if provider == "DeepL" else 3,
    }

    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            edit_page,
            **{"data": post_data},
        )
        assert response.status_code == 302
        assert response.headers.get("Location") == edit_page

        response = client.get(edit_page)

        page_translations = get_content_translations(
            Page, [2], source_language_slug, target_language_slug
        )
        source_translation = page_translations[0][source_language_slug]
        target_translation = page_translations[0][target_language_slug]

        # Check that the success message is present

        assert_message_in_log(
            f'SUCCESS  Page "{source_translation.title}" has successfully been translated ({get_english_name(source_language_slug)} ➜ {get_english_name(target_language_slug)}).',
            caplog,
        )
        # Check that the page translation exists and has the correct content
        assert target_translation.machine_translated is True
        assert target_translation.title == f"This is your translation from {provider}"
        assert (
            target_translation.content
            == f"<p>This is your translation from {provider}</p>"
        )
        # Check that used MT budget value in the region has been increased to the number of translated words
        translated_word_count = get_word_count([source_translation])
        assert (
            Region.objects.get(slug=REGION_SLUG).mt_budget_used == translated_word_count
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + WRITE_ROLES, indirect=True
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_deepl_event_automatic_translation(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    httpserver: HTTPServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check machine translation of the event when automatic_translation checkbox in set on the event form

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param httpserver: The fixture providing the dummy http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(httpserver)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{httpserver.port}"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])
    setup_google_translate_supported_languages(["en"], ["ar"])

    # Log the user in
    client, _role = login_role_user

    edit_event = reverse(
        "edit_event",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": source_language_slug,
            "event_id": 1,
        },
    )

    post_data = (
        {
            "title": "Neuer Titel",
            "content": "Neuer Inhalt",
            "automatic_translation": "on",
            "mt_translations_to_update": 2,
            "start_date": "2030-01-01",
            "end_date": "2030-01-01",
            "is_all_day": True,
            "status": status.PUBLIC,
        }
        if provider == "DeepL"
        else {
            "title": "Neuer Titel",
            "content": "Neuer Inhalt",
            "automatic_translation": "on",
            "mt_translations_to_create": 3,
            "start_date": "2030-01-01",
            "end_date": "2030-01-01",
            "is_all_day": True,
            "status": status.PUBLIC,
        }
    )

    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            edit_event,
            **{"data": post_data},
        )
        assert response.status_code == 302
        assert response.headers.get("Location") == edit_event

        response = client.get(edit_event)

        event_translations = get_content_translations(
            Event, [1], source_language_slug, target_language_slug
        )
        source_translation = event_translations[0][source_language_slug]
        target_translation = event_translations[0][target_language_slug]

        # Check that the success message is present
        assert_message_in_log(
            f'SUCCESS  Event "{source_translation.title}" has successfully been translated ({get_english_name(source_language_slug)} ➜ {get_english_name(target_language_slug)}).',
            caplog,
        )
        # Check that the page translation exists and has the correct content
        assert target_translation.machine_translated is True
        assert target_translation.title == f"This is your translation from {provider}"
        assert (
            target_translation.content
            == f"<p>This is your translation from {provider}</p>"
        )
        # Check that used MT budget value in the region has been increased to the number of translated words
        translated_word_count = get_word_count([source_translation])
        assert (
            Region.objects.get(slug=REGION_SLUG).mt_budget_used == translated_word_count
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_poi_automatic_translation(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    httpserver: HTTPServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check machine translation of the POI when automatic_translation checkbox in set on the POI form

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    :param httpserver: The fixture providing the dummy http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(httpserver)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{httpserver.port}"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])
    setup_google_translate_supported_languages(["en"], ["ar"])

    # Log the user in
    client, _role = login_role_user

    edit_poi = reverse(
        "edit_poi",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": source_language_slug,
            "poi_id": 4,
        },
    )

    post_data = {
        "title": "Neuer Titel",
        "content": "Neuer Inhalt",
        "automatic_translation": "on",
        "mt_translations_to_update": 2 if provider == "DeepL" else 3,
        "address": "Test-Straße 5",
        "postcode": "54321",
        "city": "Augsburg",
        "country": "Deutschland",
        "longitude": 1,
        "latitude": 1,
        "status": status.PUBLIC,
        "opening_hours": json.dumps(get_default_opening_hours()),
        "category": 1,
    }

    with patch.object(
        GoogleTranslateApiClient, "__init__", setup_fake_google_translate_api
    ):
        response = client.post(
            edit_poi,
            **{"data": post_data},
        )
        assert response.status_code == 302
        assert response.headers.get("Location") == edit_poi

        response = client.get(edit_poi)

        poi_translations = get_content_translations(
            POI, [4], source_language_slug, target_language_slug
        )
        source_translation = poi_translations[0][source_language_slug]
        target_translation = poi_translations[0][target_language_slug]

        # Check that the success message is present

        assert_message_in_log(
            f'SUCCESS  Location "{source_translation.title}" has successfully been translated ({get_english_name(source_language_slug)} ➜ {get_english_name(target_language_slug)}).',
            caplog,
        )
        # Check that the page translation exists and has the correct content
        assert target_translation.machine_translated is True
        assert target_translation.title == f"This is your translation from {provider}"
        assert (
            target_translation.content
            == f"<p>This is your translation from {provider}</p>"
        )
        # Check that used MT budget value in the region has been increased to the number of translated words
        translated_word_count = get_word_count([source_translation])
        assert (
            Region.objects.get(slug=REGION_SLUG).mt_budget_used == translated_word_count
        )


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

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["ar"], ["en-gb", "en-us"])
    setup_google_translate_supported_languages(["fa"], ["ar"])

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

        for page_translation in page_translations:
            # Check for a failure message
            assert_message_in_log(
                f'ERROR    Machine translations are disabled for language "{get_english_name(target_language_slug)}"',
                caplog,
            )
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

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup MT API supported languages
    setup_deepl_supported_languages(["de"], ["ar"])
    setup_google_translate_supported_languages(["en"], ["fa"])

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

        for page_translation in page_translations:
            # Check for a failure message
            assert_message_in_log(
                f'ERROR    Machine translations are disabled for language "{get_english_name(target_language_slug)}"',
                caplog,
            )
            # Check that the page was not machine translated
            assert (
                page_translation[target_language_slug] is None
                or page_translation[target_language_slug].machine_translated is False
            )
