from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client

import pytest
from django.conf import settings
from django.contrib import auth
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models.feedback.feedback import Feedback
from tests.conftest import ANONYMOUS, HIGH_PRIV_STAFF_ROLES, PRIV_STAFF_ROLES
from tests.utils import assert_message_in_log


@pytest.mark.django_db
def test_mark_admin_feedback_as_read(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # Mark feedback as read
    mark_admin_feedback_as_read = reverse("mark_admin_feedback_as_read")
    test_feedback_id = 1
    response = client.post(
        mark_admin_feedback_as_read, data={"selected_ids[]": [test_feedback_id]}
    )

    if role in PRIV_STAFF_ROLES:
        # Check for a redirect to the feedback list
        feedback_list = reverse("admin_feedback")
        assert response.status_code == 302
        assert response.headers.get("Location") == feedback_list

        # Check for a success message
        response = client.get(feedback_list)
        assert_message_in_log(
            "SUCCESS  Feedback was successfully marked as read", caplog
        )

        # Check that feedback has been marked as read by the user in the database
        feedback = Feedback.objects.get(id=test_feedback_id)
        assert feedback.read_by == auth.get_user(client)

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={mark_admin_feedback_as_read}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_mark_admin_feedback_as_unread(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # Mark feedback as unread
    mark_admin_feedback_as_unread = reverse("mark_admin_feedback_as_unread")
    test_feedback_id = 3
    response = client.post(
        mark_admin_feedback_as_unread, data={"selected_ids[]": [test_feedback_id]}
    )

    if role in PRIV_STAFF_ROLES:
        # Check for a redirect to the feedback list
        feedback_list = reverse("admin_feedback")
        assert response.status_code == 302
        assert response.headers.get("Location") == feedback_list

        # Check for a success message
        response = client.get(feedback_list)
        assert_message_in_log(
            "SUCCESS  Feedback was successfully marked as unread", caplog
        )

        # Check that feedback has been marked as unread by the user in the database
        feedback = Feedback.objects.get(id=test_feedback_id)
        assert feedback.read_by is None

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={mark_admin_feedback_as_unread}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_archive_admin_feedback(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # Archive feedback
    archive_admin_feedback = reverse("archive_admin_feedback")
    test_feedback_id = 1
    response = client.post(
        archive_admin_feedback, data={"selected_ids[]": [test_feedback_id]}
    )

    if role in PRIV_STAFF_ROLES:
        # Check for a redirect to the feedback list
        feedback_list = reverse("admin_feedback")
        assert response.status_code == 302
        assert response.headers.get("Location") == feedback_list

        # Check for a success message
        response = client.get(feedback_list)
        assert_message_in_log("SUCCESS  Feedback was successfully archived", caplog)

        # Check that feedback has been archived by the user in the database
        feedback = Feedback.objects.get(id=test_feedback_id)
        assert feedback.archived is True

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_admin_feedback}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_restore_admin_feedback(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # Restore feedback
    restore_admin_feedback = reverse("restore_admin_feedback")
    test_feedback_id = 2
    response = client.post(
        restore_admin_feedback, data={"selected_ids[]": [test_feedback_id]}
    )

    if role in PRIV_STAFF_ROLES:
        # Check for a redirect to the feedback list
        feedback_list = reverse("admin_feedback_archived")
        assert response.status_code == 302
        assert response.headers.get("Location") == feedback_list

        # Check for a success message
        response = client.get(feedback_list)
        assert_message_in_log("SUCCESS  Feedback was successfully restored", caplog)

        # Check that feedback has been restored by the user in the database
        feedback = Feedback.objects.get(id=test_feedback_id)
        assert feedback.archived is False

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={restore_admin_feedback}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_delete_admin_feedback(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # delete feedback
    delete_admin_feedback = reverse("delete_admin_feedback")
    feedback_to_delete_id = 1
    response = client.post(
        delete_admin_feedback, data={"selected_ids[]": [feedback_to_delete_id]}
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        # Check for a redirect to the feedback list
        feedback_list = reverse("admin_feedback")
        assert response.status_code == 302
        assert response.headers.get("Location") == feedback_list

        # Check for a success message
        response = client.get(feedback_list)
        assert_message_in_log("SUCCESS  Feedback was successfully deleted", caplog)

        # Check that feedback has been deleted by the user in the database
        assert not Feedback.objects.filter(id=feedback_to_delete_id)

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={delete_admin_feedback}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403
