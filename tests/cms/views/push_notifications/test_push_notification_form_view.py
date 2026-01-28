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
            "title": "German Message",
            "regions": [1, 8],
            "channel": "news",
            "mode": "ONLY_AVAILABLE",
            "submit_send": True,
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
        redirect = response.headers.get("location")
        redirect_response = client.get(redirect)

        assert (
            "News &quot;German Message&quot; requires a translation in &quot;English&quot; for &quot;Berlin&quot;"
            in redirect_response.content.decode("utf-8")
        )
