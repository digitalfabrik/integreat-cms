from __future__ import annotations

from typing import TYPE_CHECKING

from .mt_api_test import mt_setup, provider_language_combination, REGION_SLUG

if TYPE_CHECKING:
    from typing import Any

    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

    from tests.mock import MockServer

from unittest.mock import patch

import pytest
from django.urls import reverse

from integreat_cms.cms.models import Event, Page, POI, Region
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
from .google_translate_api_test import (
    setup_fake_google_translate_api,
)
from .utils import get_content_translations, get_english_name

content_role_id_combination = [
    (
        Page,
        [*PRIV_STAFF_ROLES, AUTHOR, MANAGEMENT, EDITOR],
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
    django_capture_on_commit_callbacks: Any,
) -> None:
    """
    Check for bulk machine translation of pages/events/pois via the MT API

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param content_role_id_combination: The combination of content type, user roles with permission and selected_ids used in the test
    :param settings: The fixture providing the django settings
    :param mock_server: The fixture providing the mock http server used for faking the DeepL API server
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    content_type, entitled_roles, ids = content_role_id_combination

    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, mock_server)

    # Log the user in
    client, role = login_role_user

    expected_word_count = 0
    for content_obj in content_type.objects.filter(id__in=ids):
        attrs = content_obj.get_translatable_attributes(
            ["title", "content", "meta_description"],
            source_language_slug,
            target_language_slug,
        )
        expected_word_count += word_count(attrs)

    # Translate the pois
    machine_translation = reverse(
        "machine_translation_" + content_type._meta.default_related_name,
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
        },
    )

    with (
        patch.object(
            GoogleTranslateApiClient,
            "__init__",
            setup_fake_google_translate_api,
        ),
        django_capture_on_commit_callbacks(execute=True),
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
            content_type,
            ids,
            source_language_slug,
            target_language_slug,
        )

        # Translation now happens via a Celery task (eager in tests), so
        # success surfaces through the queued report rather than a
        # synchronous Django message.
        report_url = reverse(
            "machine_translation_report",
            kwargs={
                "region_slug": REGION_SLUG,
                "language_slug": target_language_slug,
                "model_type": content_type._meta.model_name,
            },
        )
        report_response = client.get(report_url)
        report_data = report_response.json()
        assert report_data["reports"], "Expected a queued machine translation report"
        assert report_data["reports"][-1]["outcome"] == "FULL_SUCCESS"

        for translation in translations:
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

        assert (
            Region.objects.get(slug=REGION_SLUG).mt_budget_used == expected_word_count
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
    "login_role_user",
    [*PRIV_STAFF_ROLES, AUTHOR, MANAGEMENT, EDITOR],
    indirect=True,
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_bulk_mt_exceeds_limit(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    django_capture_on_commit_callbacks: Any,
) -> None:
    """
    Check for bulk machine translation error when the attempted translation would exceed the region's word limit

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param provider_language_combination: The combination of MT provider and source/target language
    :param settings: The fixture providing the django settings
    """

    provider, source_language_slug, target_language_slug = provider_language_combination

    mt_setup(["de"], ["en-gb", "en-us"], ["en"], ["ar"], settings, None)

    # Setup available translation credits to 0
    region = Region.objects.get(slug=REGION_SLUG)
    region.mt_budget_used = region.mt_budget_booked
    region.save()

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

    with (
        patch.object(
            GoogleTranslateApiClient,
            "__init__",
            setup_fake_google_translate_api,
        ),
        django_capture_on_commit_callbacks(execute=True),
    ):
        response = client.post(
            machine_translation,
            data={"selected_ids[]": selected_ids},
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
        Page,
        selected_ids,
        source_language_slug,
        target_language_slug,
    )

    # Translation now happens via a Celery task (eager in tests), so the
    # budget-exceeded failure surfaces through the queued report rather
    # than a synchronous Django message.
    report_url = reverse(
        "machine_translation_report",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
            "model_type": "page",
        },
    )
    report_response = client.get(report_url)
    report_data = report_response.json()
    assert report_data["reports"], "Expected a queued machine translation report"
    assert report_data["reports"][-1]["outcome"] == "PARTIAL_SUCCESS"

    for page_translation in page_translations:
        assert (
            page_translation[target_language_slug] is None
            or page_translation[target_language_slug].machine_translated is False
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user",
    [*PRIV_STAFF_ROLES, AUTHOR, MANAGEMENT, EDITOR],
    indirect=True,
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_bulk_mt_up_to_date(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    django_capture_on_commit_callbacks: Any,
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

    with (
        patch.object(
            GoogleTranslateApiClient,
            "__init__",
            setup_fake_google_translate_api,
        ),
        django_capture_on_commit_callbacks(execute=True),
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
    "login_role_user",
    [*PRIV_STAFF_ROLES, AUTHOR, MANAGEMENT, EDITOR],
    indirect=True,
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_bulk_mt_up_to_date_and_ready_for_mt(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    mock_server: MockServer,
    caplog: LogCaptureFixture,
    django_capture_on_commit_callbacks: Any,
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

    with (
        patch.object(
            GoogleTranslateApiClient,
            "__init__",
            setup_fake_google_translate_api,
        ),
        django_capture_on_commit_callbacks(execute=True),
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

    # The up-to-date poi is filtered out before queueing, so only the
    # ready-for-mt one is ever actually translated - translation now
    # happens via a Celery task (eager in tests), so its success
    # surfaces through the queued report rather than a synchronous
    # Django message.
    report_url = reverse(
        "machine_translation_report",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": target_language_slug,
            "model_type": "poi",
        },
    )
    report_response = client.get(report_url)
    report_data = report_response.json()
    assert report_data["reports"], "Expected a queued machine translation report"
    assert report_data["reports"][-1]["outcome"] == "FULL_SUCCESS"

    for poi_translation in poi_translations:
        # Check for a failure message if translation was already up-to-date
        if poi_translation[source_language_slug].poi_id == up_to_date_poi_id:
            assert_message_in_log(
                f'ERROR    There already is an up-to-date translation for "{poi_translation[settings.LANGUAGE_CODE].title}"',
                caplog,
            )
            assert poi_translation[target_language_slug].machine_translated is False

        # Check for a successful translation if the poi was ready for mt
        if poi_translation[source_language_slug].poi_id == ready_for_mt_poi_id:
            assert poi_translation[target_language_slug].machine_translated is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user",
    [*PRIV_STAFF_ROLES, AUTHOR, MANAGEMENT, EDITOR],
    indirect=True,
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_bulk_mt_no_source_language(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    django_capture_on_commit_callbacks: Any,
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
    with (
        patch.object(
            GoogleTranslateApiClient,
            "__init__",
            setup_fake_google_translate_api,
        ),
        django_capture_on_commit_callbacks(execute=True),
    ):
        response = client.post(
            machine_translation,
            data={"selected_ids[]": selected_ids},
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
            Page,
            selected_ids,
            target_language_slug,
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
    "login_role_user",
    [*PRIV_STAFF_ROLES, AUTHOR, MANAGEMENT, EDITOR],
    indirect=True,
)
@pytest.mark.parametrize("provider_language_combination", provider_language_combination)
def test_deepl_bulk_mt_no_target_language(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    provider_language_combination: tuple[str, str, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    django_capture_on_commit_callbacks: Any,
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
    with (
        patch.object(
            GoogleTranslateApiClient,
            "__init__",
            setup_fake_google_translate_api,
        ),
        django_capture_on_commit_callbacks(execute=True),
    ):
        response = client.post(
            machine_translation,
            data={"selected_ids[]": selected_ids},
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
            Page,
            selected_ids,
            target_language_slug,
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
