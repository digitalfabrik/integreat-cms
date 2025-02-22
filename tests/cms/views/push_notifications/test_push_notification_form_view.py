from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.urls import reverse

from tests.conftest import ANONYMOUS, PRIV_STAFF_ROLES, STAFF_ROLES

# We use Augsburg (region with German as default language) and Berlin (region with English as default language)
# to test every language is required which is the default language of at least one region of the push notification


@pytest.mark.django_db
def test_validate_forms_with_no_german_title(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Augsburg (German) is creating a push notification without German title for itself.
    This must lead to an error.
    """
    client, role = login_role_user

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    edit_push_notification = reverse(
        "new_push_notification",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )
    response = client.post(
        edit_push_notification,
        data={
            "translations-TOTAL_FORMS": "1",
            "translations-INITIAL_FORMS": "0",
            "translations-MIN_NUM_FORMS": "1",
            "translations-MAX_NUM_FORMS": "1",
            "translations-0-language": "1",
            "translations-0-title": "",
            "translations-0-text": "Test content",
            "regions": [1],
            "channel": "news",
            "mode": "ONLY_AVAILABLE",
            "submit_draft": True,
        },
    )

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_push_notification}"
        )

    if role not in STAFF_ROLES and not ANONYMOUS:
        assert response.status_code == 403

    if role in PRIV_STAFF_ROLES:
        assert "Title (German): This field is required" in response.content.decode(
            "utf-8",
        )


@pytest.mark.django_db
def test_validate_forms_with_only_german_title(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Augsburg (German) is creating a push notification with German title for itself and Berlin (English).
    This must lead to an error.
    """
    client, role = login_role_user

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    edit_push_notification = reverse(
        "edit_push_notification",
        kwargs={
            "push_notification_id": 8,
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )
    response = client.post(
        edit_push_notification,
        data={
            "translations-TOTAL_FORMS": "2",
            "translations-INITIAL_FORMS": "0",
            "translations-MIN_NUM_FORMS": "1",
            "translations-MAX_NUM_FORMS": "1",
            "translations-0-language": "1",
            "translations-0-title": "German title",
            "translations-0-text": "Test content",
            "translations-1-language": "2",
            "translations-1-title": "",
            "translations-1-text": "Test content",
            "regions": [1, 8],
            "channel": "news",
            "mode": "ONLY_AVAILABLE",
            "submit_draft": True,
        },
    )

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_push_notification}"
        )

    if role not in STAFF_ROLES and not ANONYMOUS:
        assert response.status_code == 403

    if role in PRIV_STAFF_ROLES:
        assert "Title (English): This field is required" in response.content.decode(
            "utf-8",
        )
