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
def test_cross_region_edit_blocked(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Attempting to edit a push notification belonging to another region
    must return a 404 (see #4612).
    """
    client, role = login_role_user

    # Push notification 6 belongs to Nürnberg (id=2), not Augsburg (id=1)
    cross_region_url = reverse(
        "edit_push_notification",
        kwargs={
            "push_notification_id": 6,
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )
    initial_count = PushNotification.objects.count()

    get_response = client.get(cross_region_url)
    if role == ANONYMOUS:
        assert get_response.status_code == 302
        return
    if not get_response.wsgi_request.user.has_perm("cms.view_pushnotification"):
        assert get_response.status_code == 403
        return
    assert get_response.status_code == 404

    original_german_news = PushNotification.objects.get(id=6).get_translation("de")
    original_german_title = original_german_news.title
    original_german_text = original_german_news.text

    new_title = "Cross Region Edit"
    new_text = "Cross region text"

    assert original_german_title != new_title
    assert original_german_text != new_text

    post_response = client.post(
        cross_region_url,
        data={
            "title": new_title,
            "text": new_text,
            "regions": [2],
            "channel": "news",
            "mode": "ONLY_AVAILABLE",
            "submit_update": True,
        },
    )
    if not post_response.wsgi_request.user.has_perm("cms.change_pushnotification"):
        assert post_response.status_code == 403
        return

    assert post_response.status_code == 404
    assert PushNotification.objects.count() == initial_count

    german_news = PushNotification.objects.get(id=6).get_translation("de")
    german_title = german_news.title
    german_text = german_news.text

    assert original_german_title == german_title
    assert original_german_text == german_text


@pytest.mark.django_db
def test_non_existent_push_notification_edit_blocked(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Submitting an edit for a non-existent push notification ID must return a 404
    instead of inadvertently creating a new push notification (see #4612).
    """
    client, role = login_role_user

    non_existent_url = reverse(
        "edit_push_notification",
        kwargs={
            "push_notification_id": 99999,
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )
    initial_count = PushNotification.objects.count()

    get_response = client.get(non_existent_url)
    if role == ANONYMOUS:
        assert get_response.status_code == 302
        return
    if not get_response.wsgi_request.user.has_perm("cms.view_pushnotification"):
        assert get_response.status_code == 403
        return
    assert get_response.status_code == 404

    post_response = client.post(
        non_existent_url,
        data={
            "title": "Non-existent PN",
            "text": "Non-existent text",
            "regions": [1],
            "channel": "news",
            "mode": "ONLY_AVAILABLE",
            "submit_update": True,
        },
    )
    if not post_response.wsgi_request.user.has_perm("cms.change_pushnotification"):
        assert post_response.status_code == 403
        return

    assert post_response.status_code == 404
    assert PushNotification.objects.count() == initial_count
