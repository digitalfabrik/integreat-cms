from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.test.client import Client
    from pytest_django.fixtures import Settings

import pytest
from django.urls import reverse

from integreat_cms.cms.models import PushNotification, Region
from tests.constants import ANONYMOUS, PRIV_STAFF_ROLES, STAFF_ROLES

# We use Augsburg (region with German as default language) and Berlin (region with English as default language)
# to test every language is required which is the default language of at least one region of the push notification


@pytest.mark.django_db
def test_validate_forms_with_only_german_title(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: Settings,
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


@pytest.mark.django_db
def test_invalid_new_translation_keeps_language_tabs(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Submitting an invalid form for a language without an existing translation
    must still show the tabs of all other languages (see #4126).
    """
    client, role = login_role_user

    # Push notification 2 of Augsburg only has a German translation
    edit_push_notification = reverse(
        "edit_push_notification",
        kwargs={
            "push_notification_id": 2,
            "region_slug": "augsburg",
            "language_slug": "en",
        },
    )
    response = client.post(
        edit_push_notification,
        data={
            "title": "English title",
            "text": "x" * 501,
            "regions": [1],
            "channel": "news",
            "mode": "ONLY_AVAILABLE",
            "submit_update": True,
        },
    )

    if role == ANONYMOUS:
        assert response.status_code == 302
        return
    if not response.wsgi_request.user.has_perm("cms.change_pushnotification"):
        assert response.status_code == 403
        return
    assert response.status_code == 200
    region = Region.objects.get(slug="augsburg")
    assert list(response.context["languages"]) == list(region.active_languages)


@pytest.mark.django_db
def test_saved_news_form_shows_permitted_actions(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """Saved news should offer the same permitted actions as the list view."""
    client, _ = login_role_user
    edit_push_notification = reverse(
        "edit_push_notification",
        kwargs={
            "push_notification_id": 2,
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.get(edit_push_notification)

    if response.status_code != 200:
        return

    content = response.content.decode("utf-8")
    push_notification = PushNotification.objects.get(id=2)
    action_kwargs = {
        "push_notification_id": push_notification.id,
        "region_slug": "augsburg",
        "language_slug": "de",
    }
    if response.wsgi_request.user.has_perm("cms.archive_pushnotification"):
        action_name = (
            "restore_push_notification"
            if push_notification.archived
            else "archive_push_notification"
        )
        action_url = reverse(action_name, kwargs=action_kwargs)
        assert f'data-action="{action_url}"' in content
    else:
        archive_url = reverse("archive_push_notification", kwargs=action_kwargs)
        restore_url = reverse("restore_push_notification", kwargs=action_kwargs)
        assert f'data-action="{archive_url}"' not in content
        assert f'data-action="{restore_url}"' not in content
    if response.wsgi_request.user.has_perm("cms.delete_pushnotification"):
        delete_url = reverse("delete_push_notification", kwargs=action_kwargs)
        assert f'data-action="{delete_url}"' in content
    else:
        delete_url = reverse("delete_push_notification", kwargs=action_kwargs)
        assert f'data-action="{delete_url}"' not in content
