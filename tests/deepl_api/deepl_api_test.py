from __future__ import annotations

import json
from html import unescape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Final

    from _pytest.logging import LogCaptureFixture
    from django.db.models.base import ModelBase
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.apps import apps
from django.urls import reverse
from django.utils.html import strip_tags

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Page,
    PageTranslation,
    POI,
    POITranslation,
    Region,
)
from integreat_cms.cms.models.pois.poi import get_default_opening_hours
from integreat_cms.cms.utils.stringify_list import iter_to_string
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

# Slugs we want to use for testing
REEGION_SLUG: Final[str] = "augsburg"
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
                }
            ]
        },
    )


def setup_deepl_supported_languages(
    source_languages: list[str], target_languages: list[str]
) -> None:
    """
    Setup DeepL API supported languages

    :param source_languages: The supported source languages
    :param target_languages: The supported target languages
    """
    apps.get_app_config("deepl_api").supported_source_languages = source_languages
    apps.get_app_config("deepl_api").supported_target_languages = target_languages


def get_content_translations(
    content_model: ModelBase, ids: list[int], *language_slugs: str
) -> list[dict[str, Any]]:
    """
    Load the translations for the given content model from the database

    :param content_model: Name of the requested data model (Page, Event or POI)
    :param ids: List of ids of the requested model entries
    :param language_slugs: List of the requested language slugs
    :return: Content translations
    """
    return [
        {
            "content_entry": content_entry,
            **{slug: content_entry.get_translation(slug) for slug in language_slugs},
        }
        for content_entry in content_model.objects.filter(id__in=ids)
    ]


def get_word_count(
    translations: list[EventTranslation] | (
        list[PageTranslation] | list[POITranslation]
    ),
) -> int:
    """
    Count the total number of words in the title, content and meta-description of translations

    :param translations: List of translations (Pages, Events or POIs)
    :return: Word count
    """
    word_count = 0
    for translation in translations:
        attr_to_count = [translation.title, translation.content]
        if isinstance(translation, POITranslation):
            # Currently only POI translations have a meta_description
            attr_to_count.append(translation.meta_description)
        content_to_count_list = [
            unescape(strip_tags(attr)) for attr in attr_to_count if attr
        ]
        content_to_count = " ".join(content_to_count_list)
        for char in "-;:,;!?\n":
            content_to_count = content_to_count.replace(char, " ")
        word_count += len(content_to_count.split())
    return word_count


@pytest.mark.django_db
def test_deepl_bulk_mt_pages(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation of pages via the DeepL API

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(mock_server)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, role = login_role_user

    # Translate the pages
    selected_ids = [2, 3, 6]
    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    response = client.post(machine_translation, data={"selected_ids[]": selected_ids})
    print(response.headers)

    if role in PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR]:
        # If the role should be allowed to access the view, we expect a successful result
        assert response.status_code == 302
        page_tree = reverse(
            "pages",
            kwargs={
                "region_slug": REEGION_SLUG,
                "language_slug": TARGET_LANGUAGE_SLUG,
            },
        )
        assert response.headers.get("Location") == page_tree
        response = client.get(page_tree)

        # Get the page objects including their translations from the database
        page_translations = get_content_translations(
            Page, selected_ids, SOURCE_LANGUAGE_SLUG, TARGET_LANGUAGE_SLUG
        )
        # Check that the success message are present
        assert_message_in_log(
            'SUCCESS  The following pages have successfully been translated (German ➜ English): "Über die App Integreat Augsburg", "Willkommen in Augsburg" and "Kontakt zu App Team Augsburg"',
            caplog,
        )
        for page_translation in page_translations:
            # Check that the page translation exists and really has the correct content
            assert page_translation[TARGET_LANGUAGE_SLUG].machine_translated is True
            assert (
                page_translation[TARGET_LANGUAGE_SLUG].title
                == "This is your translation from DeepL"
            )
            assert (
                page_translation[TARGET_LANGUAGE_SLUG].content
                == "<p>This is your translation from DeepL</p>"
            )
        # Check that used MT budget value in the region has been increased to the number of translated words
        translated_word_count = get_word_count(
            [
                page_translation[SOURCE_LANGUAGE_SLUG]
                for page_translation in page_translations
            ]
        )
        assert (
            Region.objects.get(slug=REEGION_SLUG).mt_budget_used
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
def test_deepl_bulk_mt_pois(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation of pois via the DeepL API

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(mock_server)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, role = login_role_user
    # Translate the pois
    selected_ids = [6]
    machine_translation = reverse(
        "machine_translation_pois",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    response = client.post(machine_translation, data={"selected_ids[]": selected_ids})
    print(response.headers)

    if role in PRIV_STAFF_ROLES + WRITE_ROLES:
        # If the role should be allowed to access the view, we expect a successful result
        assert response.status_code == 302
        poi_tree = reverse(
            "pois",
            kwargs={
                "region_slug": REEGION_SLUG,
                "language_slug": TARGET_LANGUAGE_SLUG,
            },
        )
        assert response.headers.get("Location") == poi_tree
        response = client.get(poi_tree)

        poi_translations = get_content_translations(
            POI, selected_ids, SOURCE_LANGUAGE_SLUG, TARGET_LANGUAGE_SLUG
        )

        for poi_translation in poi_translations:
            assert_message_in_log(
                f'SUCCESS  Location "{poi_translation[SOURCE_LANGUAGE_SLUG]}" has successfully been translated (German ➜ English).',
                caplog,
            )
            # Check that the page translation exists and really has the correct content
            assert poi_translation[TARGET_LANGUAGE_SLUG].machine_translated is True
            assert (
                poi_translation[TARGET_LANGUAGE_SLUG].title
                == "This is your translation from DeepL"
            )
            assert (
                poi_translation[TARGET_LANGUAGE_SLUG].content
                == "<p>This is your translation from DeepL</p>"
            )
            if poi_translation[TARGET_LANGUAGE_SLUG].meta_description:
                assert (
                    poi_translation[TARGET_LANGUAGE_SLUG].meta_description
                    == "This is your translation from DeepL"
                )

        # Check that used MT budget value in the region has been increased to the number of translated words
        translated_word_count = get_word_count(
            [
                poi_translation[SOURCE_LANGUAGE_SLUG]
                for poi_translation in poi_translations
            ]
        )
        assert (
            Region.objects.get(slug=REEGION_SLUG).mt_budget_used
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
def test_deepl_bulk_mt_events(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation of events via the DeepL API

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(mock_server)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, role = login_role_user
    # Translate the events
    selected_ids = [1]
    machine_translation = reverse(
        "machine_translation_events",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    response = client.post(machine_translation, data={"selected_ids[]": selected_ids})
    print(response.headers)

    if role in PRIV_STAFF_ROLES + WRITE_ROLES:
        # If the role should be allowed to access the view, we expect a successful result
        assert response.status_code == 302
        event_tree = reverse(
            "events",
            kwargs={
                "region_slug": REEGION_SLUG,
                "language_slug": TARGET_LANGUAGE_SLUG,
            },
        )
        assert response.headers.get("Location") == event_tree
        response = client.get(event_tree)

        event_translations = get_content_translations(
            Event, selected_ids, SOURCE_LANGUAGE_SLUG, TARGET_LANGUAGE_SLUG
        )

        for event_translation in event_translations:
            assert_message_in_log(
                f'SUCCESS  Event "{event_translation[SOURCE_LANGUAGE_SLUG]}" has successfully been translated (German ➜ English).',
                caplog,
            )
            # Check that the page translation exists and really has the correct content
            assert event_translation[TARGET_LANGUAGE_SLUG].machine_translated is True
            assert (
                event_translation[TARGET_LANGUAGE_SLUG].title
                == "This is your translation from DeepL"
            )
            assert (
                event_translation[TARGET_LANGUAGE_SLUG].content
                == "<p>This is your translation from DeepL</p>"
            )

        # Check that used MT budget value in the region has been increased to the number of translated words
        translated_word_count = get_word_count(
            [
                event_translation[SOURCE_LANGUAGE_SLUG]
                for event_translation in event_translations
            ]
        )
        assert (
            Region.objects.get(slug=REEGION_SLUG).mt_budget_used
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
def test_deepl_bulk_mt_exceeds_limit(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation error when the attempted translation would exceed the region's word limit

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Setup available translation credits to 0
    settings.MT_CREDITS_FREE = 0

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    selected_ids = [2, 3, 6]
    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    response = client.post(machine_translation, data={"selected_ids[]": selected_ids})
    print(response.headers)

    assert response.status_code == 302
    page_tree = reverse(
        "pages",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    assert response.headers.get("Location") == page_tree
    response = client.get(page_tree)

    # Get the page objects including their translations from the database
    page_translations = get_content_translations(
        Page, selected_ids, SOURCE_LANGUAGE_SLUG, TARGET_LANGUAGE_SLUG
    )

    # Check for a failure message
    translations_str = iter_to_string(
        [t[SOURCE_LANGUAGE_SLUG].title for t in page_translations]
    )
    assert_message_in_log(
        f"ERROR    The following pages could not be translated because they would exceed the remaining budget of 0 words: {translations_str}",
        caplog,
    )
    for page_translation in page_translations:
        assert (
            page_translation[TARGET_LANGUAGE_SLUG] is None
            or page_translation[TARGET_LANGUAGE_SLUG].machine_translated is False
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
def test_deepl_bulk_mt_up_to_date(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation error when one of the target translations is up-to-date and the other is machine translated

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    up_to_date_page_id = 1
    machine_translated_page_id = 16

    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )

    response = client.post(
        machine_translation,
        data={"selected_ids[]": [up_to_date_page_id, machine_translated_page_id]},
    )
    print(response.headers)

    assert response.status_code == 302
    page_tree = reverse(
        "pages",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
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
def test_deepl_bulk_mt_up_to_date_and_ready_for_mt(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation when one of the target translations is up-to-date and the other is ready for MT

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the dummy http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(mock_server)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, _role = login_role_user

    # Translate the pois
    up_to_date_poi_id = 4
    ready_for_mt_poi_id = 6

    machine_translation = reverse(
        "machine_translation_pois",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )

    response = client.post(
        machine_translation,
        data={"selected_ids[]": [up_to_date_poi_id, ready_for_mt_poi_id]},
    )
    print(response.headers)

    assert response.status_code == 302
    poi_tree = reverse(
        "pois",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    assert response.headers.get("Location") == poi_tree
    response = client.get(poi_tree)

    poi_translations = get_content_translations(
        POI,
        [up_to_date_poi_id, ready_for_mt_poi_id],
        SOURCE_LANGUAGE_SLUG,
        TARGET_LANGUAGE_SLUG,
    )

    for poi_translation in poi_translations:
        # Check for a failure message if translation was already up-to-date
        if poi_translation[SOURCE_LANGUAGE_SLUG].poi_id == up_to_date_poi_id:
            assert_message_in_log(
                f'ERROR    There already is an up-to-date translation for "{poi_translation[TARGET_LANGUAGE_SLUG].title}"',
                caplog,
            )
            assert poi_translation[TARGET_LANGUAGE_SLUG].machine_translated is False

        # Check for a successful message if translation was ready for mt
        if poi_translation[SOURCE_LANGUAGE_SLUG].poi_id == ready_for_mt_poi_id:
            assert_message_in_log(
                f'SUCCESS  Location "{poi_translation[SOURCE_LANGUAGE_SLUG]}" has successfully been translated (German ➜ English).',
                caplog,
            )
            assert poi_translation[TARGET_LANGUAGE_SLUG].machine_translated is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
def test_deepl_page_automatic_translation(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check machine translation of the page when automatic_translation checkbox in set on the page form

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(mock_server)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, _role = login_role_user

    edit_page = reverse(
        "edit_page",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": SOURCE_LANGUAGE_SLUG,
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
        "mt_translations_to_create": 2,
    }

    response = client.post(
        edit_page,
        **{"data": post_data},
    )
    assert response.status_code == 302
    assert response.headers.get("Location") == edit_page

    response = client.get(edit_page)

    page_translations = get_content_translations(
        Page, [2], SOURCE_LANGUAGE_SLUG, TARGET_LANGUAGE_SLUG
    )
    source_translation = page_translations[0][SOURCE_LANGUAGE_SLUG]
    target_translation = page_translations[0][TARGET_LANGUAGE_SLUG]

    # Check that the success message is present
    assert_message_in_log(
        f'SUCCESS  Page "{source_translation.title}" has successfully been translated (German ➜ English).',
        caplog,
    )
    # Check that the page translation exists and has the correct content
    assert target_translation.machine_translated is True
    assert target_translation.title == "This is your translation from DeepL"
    assert target_translation.content == "<p>This is your translation from DeepL</p>"
    # Check that used MT budget value in the region has been increased to the number of translated words
    translated_word_count = get_word_count([source_translation])
    assert Region.objects.get(slug=REEGION_SLUG).mt_budget_used == translated_word_count


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + WRITE_ROLES, indirect=True
)
def test_deepl_event_automatic_translation(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check machine translation of the event when automatic_translation checkbox in set on the event form

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(mock_server)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, _role = login_role_user

    edit_event = reverse(
        "edit_event",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": SOURCE_LANGUAGE_SLUG,
            "event_id": 1,
        },
    )

    post_data = {
        "title": "Neuer Titel",
        "content": "Neuer Inhalt",
        "automatic_translation": "on",
        "mt_translations_to_update": 2,
        "start_date": "2030-01-01",
        "end_date": "2030-01-01",
        "is_all_day": True,
        "status": status.PUBLIC,
    }

    response = client.post(
        edit_event,
        **{"data": post_data},
    )
    assert response.status_code == 302
    assert response.headers.get("Location") == edit_event

    response = client.get(edit_event)

    event_translations = get_content_translations(
        Event, [1], SOURCE_LANGUAGE_SLUG, TARGET_LANGUAGE_SLUG
    )
    source_translation = event_translations[0][SOURCE_LANGUAGE_SLUG]
    target_translation = event_translations[0][TARGET_LANGUAGE_SLUG]

    # Check that the success message is present
    assert_message_in_log(
        f'SUCCESS  Event "{source_translation.title}" has successfully been translated (German ➜ English).',
        caplog,
    )
    # Check that the page translation exists and has the correct content
    assert target_translation.machine_translated is True
    assert target_translation.title == "This is your translation from DeepL"
    assert target_translation.content == "<p>This is your translation from DeepL</p>"
    # Check that used MT budget value in the region has been increased to the number of translated words
    translated_word_count = get_word_count([source_translation])
    assert Region.objects.get(slug=REEGION_SLUG).mt_budget_used == translated_word_count


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
def test_deepl_poi_automatic_translation(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check machine translation of the POI when automatic_translation checkbox in set on the POI form

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup a mocked DeepL API server with dummy response
    setup_fake_deepl_api_server(mock_server)

    # Redirect call aimed at the DeepL API to the fake server
    settings.DEEPL_API_URL = f"http://localhost:{mock_server.port}"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["en-gb", "en-us"])

    # Log the user in
    client, _role = login_role_user

    edit_poi = reverse(
        "edit_poi",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": SOURCE_LANGUAGE_SLUG,
            "poi_id": 4,
        },
    )

    post_data = {
        "title": "Neuer Titel",
        "content": "Neuer Inhalt",
        "automatic_translation": "on",
        "mt_translations_to_update": 2,
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

    response = client.post(
        edit_poi,
        **{"data": post_data},
    )
    assert response.status_code == 302
    assert response.headers.get("Location") == edit_poi

    response = client.get(edit_poi)

    poi_translations = get_content_translations(
        POI, [4], SOURCE_LANGUAGE_SLUG, TARGET_LANGUAGE_SLUG
    )
    source_translation = poi_translations[0][SOURCE_LANGUAGE_SLUG]
    target_translation = poi_translations[0][TARGET_LANGUAGE_SLUG]

    # Check that the success message is present
    assert_message_in_log(
        f'SUCCESS  Location "{source_translation.title}" has successfully been translated (German ➜ English).',
        caplog,
    )
    # Check that the page translation exists and has the correct content
    assert target_translation.machine_translated is True
    assert target_translation.title == "This is your translation from DeepL"
    assert target_translation.content == "<p>This is your translation from DeepL</p>"
    # Check that used MT budget value in the region has been increased to the number of translated words
    translated_word_count = get_word_count([source_translation])
    assert Region.objects.get(slug=REEGION_SLUG).mt_budget_used == translated_word_count


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
def test_deepl_bulk_mt_no_source_language(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation error when the source language is not available

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["ar"], ["en-gb", "en-us"])

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    selected_ids = [1, 2, 3]
    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    response = client.post(machine_translation, data={"selected_ids[]": selected_ids})
    print(response.headers)

    assert response.status_code == 302
    page_tree = reverse(
        "pages",
        kwargs={
            "region_slug": REEGION_SLUG,
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
            'ERROR    Machine translations are disabled for language "English"',
            caplog,
        )
        # Check that the page was not machine translated
        assert (
            page_translation[TARGET_LANGUAGE_SLUG] is None
            or page_translation[TARGET_LANGUAGE_SLUG].machine_translated is False
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [AUTHOR, MANAGEMENT, EDITOR], indirect=True
)
def test_deepl_bulk_mt_no_target_language(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for bulk machine translation error when the target language is not available

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # Setup DeepL API supported languages
    setup_deepl_supported_languages(["de"], ["ar"])

    # Log the user in
    client, _role = login_role_user

    # Translate the pages
    selected_ids = [1, 2, 3]
    machine_translation = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    response = client.post(machine_translation, data={"selected_ids[]": selected_ids})
    print(response.headers)

    assert response.status_code == 302
    page_tree = reverse(
        "pages",
        kwargs={
            "region_slug": REEGION_SLUG,
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
            'ERROR    Machine translations are disabled for language "English"',
            caplog,
        )
        # Check that the page was not machine translated
        assert (
            page_translation[TARGET_LANGUAGE_SLUG] is None
            or page_translation[TARGET_LANGUAGE_SLUG].machine_translated is False
        )


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
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    Check for error handling when DeepL API returns server error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param error: The error status to test
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    :param caplog: The :fixture:`caplog` fixture
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
            "region_slug": REEGION_SLUG,
            "language_slug": TARGET_LANGUAGE_SLUG,
        },
    )
    response = client.post(machine_translation, data={"selected_ids[]": selected_ids})
    print(response.headers)

    assert response.status_code == 302
    page_tree = reverse(
        "pages",
        kwargs={
            "region_slug": REEGION_SLUG,
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
