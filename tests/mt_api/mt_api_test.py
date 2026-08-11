from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING

from integreat_cms.cms.constants.translation_status import (
    MACHINE_TRANSLATED,
    UP_TO_DATE,
)

if TYPE_CHECKING:
    from typing import Any, Final

    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

    from tests.mock import MockServer

from unittest.mock import patch

import pytest
from django.urls import resolve, reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Event, Language, Page, PageTranslation, POI, Region
from integreat_cms.cms.models.pois.poi import get_default_opening_hours
from integreat_cms.core.utils.word_count import word_count
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
from .utils import get_content_translations, get_english_name

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


# Fixture for form translation test
content_role_id_data_combination = [
    (
        Page,
        [*PRIV_STAFF_ROLES, AUTHOR, MANAGEMENT, EDITOR],
        4,
        {
            "title": "Neuer Titel",
            "content": "Neuer Inhalt",
            "mirrored_page_region": "",
            "treebeard_ref_node": 3,
            "treebeard_position": "right",
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
            "primary_email": "",
            "primary_website": "",
            "primary_phone_number": "",
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
            "has_not_location": True,
        },
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
@pytest.mark.parametrize(
    "content_role_id_data_combination",
    content_role_id_data_combination,
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

    # Compute expected word count from the form data that will be submitted.
    # We can't use get_translatable_attributes here because the form POST
    # changes the source translation before MT runs.
    expected_word_count = word_count(
        [
            (attr, data[attr])
            for attr in ["title", "content", "meta_description"]
            if data.get(attr)
        ]
    )

    # Get "page" from PAGE, "poi" from POI and "event" from EVENT
    content_name = content_type._meta.verbose_name if content_type is not POI else "poi"

    create_or_update = (
        "update"
        if content_type.objects.filter(
            id=content_id,
            translations__language__slug=target_language_slug,
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
            "mt_translations_to_" + create_or_update: Language.objects.filter(
                slug=target_language_slug,
            )
            .first()
            .id,
            "status": (
                status.REVIEW
                if content_type is Page and role is AUTHOR
                else status.PUBLIC
            ),
        },
    )

    with patch.object(
        GoogleTranslateApiClient,
        "__init__",
        setup_fake_google_translate_api,
    ):
        response = client.post(
            edit_content,
            **{"data": data},  # noqa: PIE804
        )

        if role in entitled_roles:
            # If the role should be allowed to access the view, we expect a successful result
            translations = get_content_translations(
                content_type,
                [content_id],
                source_language_slug,
                target_language_slug,
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
            assert (
                Region.objects.get(slug=REGION_SLUG).mt_budget_used
                == expected_word_count
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


do_not_translate_title = [True, False]


@pytest.mark.django_db
@pytest.mark.parametrize("do_not_translate_title", do_not_translate_title)
@pytest.mark.parametrize(
    "login_role_user",
    [*PRIV_STAFF_ROLES, MANAGEMENT, EDITOR],
    indirect=True,
)
def test_do_not_translate_title(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    do_not_translate_title: bool,
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    Check `do_not_translate_title` flag works as expected

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param do_not_translate_title: The value of `do_not_translate_title` flag
    :param settings: The fixture providing the django settings
    :param caplog: The :fixture:`caplog` fixture
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    """
    client, _role = login_role_user

    region = Region.objects.get(slug=REGION_SLUG)

    page_id = _create_page(client, REGION_SLUG, "xxxx", "xxxx", "")

    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, mock_server)

    with patch.object(
        GoogleTranslateApiClient,
        "__init__",
        setup_fake_google_translate_api,
    ):
        _edit_translation(
            client,
            page_id,
            "de",
            "Neuer Titel",
            "Neuer Inhalt",
            region=region,
            mt_translations_to_create="en",
            do_not_translate_title=do_not_translate_title,
        )

        de_translation = PageTranslation.objects.filter(
            page__id=page_id, language__slug="de"
        ).first()
        en_translation = PageTranslation.objects.filter(
            page__id=page_id, language__slug="en"
        ).first()

        assert de_translation
        assert en_translation
        assert en_translation.translation_state == MACHINE_TRANSLATED

        if do_not_translate_title:
            assert en_translation.title == de_translation.title
        else:
            assert en_translation.title == "This is your translation from DeepL"

        _edit_translation(
            client,
            page_id,
            "en",
            "Title in English",
            "New content",
            region=region,
            mt_translations_to_create="ar",
            do_not_translate_title=do_not_translate_title,
        )

        en_translation = PageTranslation.objects.filter(
            page__id=page_id, language__slug="en"
        ).first()
        ar_translation = PageTranslation.objects.filter(
            page__id=page_id, language__slug="ar"
        ).first()

        assert en_translation
        assert ar_translation
        assert ar_translation.translation_state == MACHINE_TRANSLATED

        if do_not_translate_title:
            assert ar_translation.title == en_translation.title
        else:
            assert (
                ar_translation.title == "This is your translation from Google Translate"
            )


@pytest.mark.django_db
@pytest.mark.parametrize("login_role_user", [EDITOR], indirect=True)
def test_mt_update_to_empty_content(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    When a page is updated with empty content and MT updates are enabled:
    - target translation content is cleared without calling the MT API
    - target translations are marked as machine translated
    - the minor_edit flag is set to False
    """
    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, mock_server)

    client, _role = login_role_user

    region = Region.objects.get(slug=REGION_SLUG)

    # Create initial translations
    page_id = _create_page(client, REGION_SLUG, "Titel", "titel", "<p>Inhalt</p>")
    _edit_translation(client, page_id, "en", "Title", "<p>Content</p>")
    _edit_translation(client, page_id, "ar", "العنوان", "<p>العنوان</p>")

    # Trigger automatic translations
    with patch.object(
        GoogleTranslateApiClient,
        "__init__",
        setup_fake_google_translate_api,
    ):
        _edit_translation(
            client,
            page_id,
            language_slug="de",
            title="Titel",
            content="",
            region=region,
            mt_translations_to_update="en",
        )

        en_translation = PageTranslation.objects.filter(
            page__id=page_id, language__slug="en"
        ).first()

        assert en_translation
        assert en_translation.title == "Title"
        assert en_translation.content == ""
        assert en_translation.translation_state == MACHINE_TRANSLATED
        assert en_translation.minor_edit is False
        assert mock_server.requests_counter == 0

        _edit_translation(
            client,
            page_id,
            language_slug="en",
            title="Title",
            content="",
            region=region,
            mt_translations_to_update="ar",
        )

        ar_translation = PageTranslation.objects.filter(
            page__id=page_id, language__slug="ar"
        ).first()

        assert ar_translation
        assert ar_translation.title == "العنوان"
        assert ar_translation.content == ""
        assert ar_translation.translation_state == MACHINE_TRANSLATED
        assert ar_translation.minor_edit is False
        assert mock_server.requests_counter == 0


@pytest.mark.django_db
@pytest.mark.parametrize("login_role_user", [EDITOR], indirect=True)
def test_mt_update_up_to_date_no_changes(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
) -> None:
    """
    When a source translation is updated without changes and MT update is enabled but target translation is already up-to-date:
    - target translation is not updated
    - failure message is displayed
    """
    mt_setup(["de"], ["en-gb", "en-us"], [], [], settings, mock_server)

    client, _role = login_role_user

    region = Region.objects.get(slug=REGION_SLUG)

    # Create initial translations
    page_id = _create_page(client, REGION_SLUG, "Titel", "titel", "<p>Inhalt</p>")
    _edit_translation(client, page_id, "en", "Title", "<p>Content</p>")

    en_translation = PageTranslation.objects.filter(
        page__id=page_id, language__slug="en"
    ).first()

    assert en_translation
    assert en_translation.translation_state == UP_TO_DATE

    # Trigger automatic translations
    _edit_translation(
        client,
        page_id,
        language_slug="de",
        title="Titel",
        content="<p>Inhalt</p>",
        region=region,
        mt_translations_to_update="en",
    )

    # Check for a failure message
    assert_message_in_log(
        "ERROR    Page \"Title\" was not translated into 'English', because there were no changes to the source translation.",
        caplog,
    )
    en_translation = PageTranslation.objects.filter(
        page__id=page_id, language__slug="en"
    ).first()

    assert en_translation
    assert en_translation.machine_translated is False
    assert en_translation.translation_state == UP_TO_DATE


@pytest.mark.django_db
@pytest.mark.parametrize("login_role_user", [EDITOR], indirect=True)
def test_manual_update_mt_page(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
) -> None:
    """
    When a machine-translated page is manually updated without any changes:
    - the translation status is set to up-to-date
    - the minor_edit flag is set to True
    """
    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, mock_server)

    client, _role = login_role_user

    region = Region.objects.get(slug=REGION_SLUG)

    # Create initial translations
    page_id = _create_page(client, REGION_SLUG, "Titel", "titel", "<p>Inhalt</p>")

    # Trigger automatic translations
    with patch.object(
        GoogleTranslateApiClient,
        "__init__",
        setup_fake_google_translate_api,
    ):
        _edit_translation(
            client,
            page_id,
            language_slug="de",
            title="Titel",
            content="<p>Inhalt</p>",
            region=region,
            mt_translations_to_create="en",
        )

        en_translation = PageTranslation.objects.filter(
            page__id=page_id, language__slug="en"
        ).first()

        assert en_translation
        assert en_translation.translation_state == MACHINE_TRANSLATED
        assert en_translation.minor_edit is False

        # Manual update without content changes
        _edit_translation(
            client,
            page_id,
            language_slug="en",
            title=en_translation.title,
            content=en_translation.content,
            region=region,
        )

        en_translation = PageTranslation.objects.filter(
            page__id=page_id, language__slug="en"
        ).first()

        assert en_translation
        assert en_translation.translation_state == UP_TO_DATE
        assert en_translation.minor_edit is True


def _create_page(
    client: Client,
    region_slug: str,
    title: str,
    slug: str,
    content: str,
) -> Page:
    url = reverse(
        "new_page",
        kwargs={
            "region_slug": region_slug,
            "language_slug": "de",
        },
    )
    data = {
        "status": "PUBLIC",
        "content": content,
        "title": title,
        "slug": slug,
        "icon": "",
        "treebeard_ref_node": 28,
        "treebeard_position": "left",
        "parent": "",
        "mirrored_page_region": "",
        "mirrored_page_first": True,
        "api_token": "",
        "authors": "",
        "editors": "",
        "organization": "",
        "minor_edit": False,
    }
    response = client.post(url, data=data)
    assert response.status_code == 302
    edit_page_url = response.headers.get("location")

    return resolve(edit_page_url).kwargs["page_id"]


def _edit_translation(
    client: Client,
    page_id: str,
    language_slug: str,
    title: str,
    content: str,
    *,
    region: Region | None = None,
    mt_translations_to_create: str | None = None,
    mt_translations_to_update: str | None = None,
    do_not_translate_title: bool = False,
) -> None:
    url = reverse(
        "edit_page",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": language_slug,
            "page_id": page_id,
        },
    )
    data = {
        "title": title,
        "content": content,
        "minor_edit": False,
        "do_not_translate_title": do_not_translate_title,
        "mirrored_page_region": "",
        "status": status.PUBLIC,
        "treebeard_position": "right",
    }

    if mt_translations_to_create or mt_translations_to_update:
        assert region is not None
        data["automatic_translation"] = "on"
        if mt_translations_to_create:
            data["mt_translations_to_create"] = region.language_tree_nodes.get(
                language__slug=mt_translations_to_create
            ).id
        if mt_translations_to_update:
            data["mt_translations_to_update"] = region.language_tree_nodes.get(
                language__slug=mt_translations_to_update
            ).id

    client.post(url, data=data)
