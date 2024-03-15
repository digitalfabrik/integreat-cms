from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client

import csv
from io import StringIO

import pytest
from django.conf import settings
from django.contrib import auth
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models.feedback.feedback import Feedback
from tests.conftest import (
    ANONYMOUS,
    HIGH_PRIV_STAFF_ROLES,
    MANAGEMENT,
    PRIV_STAFF_ROLES,
    STAFF_ROLES,
)
from tests.utils import assert_message_in_log

region_slug_param = {"region_slug": "augsburg"}


@pytest.mark.django_db
def test_mark_region_feedback_as_read(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # Mark feedback as read
    mark_region_feedback_as_read = reverse(
        "mark_region_feedback_as_read", kwargs=region_slug_param
    )
    test_feedback_id = 4
    response = client.post(
        mark_region_feedback_as_read, data={"selected_ids[]": [test_feedback_id]}
    )

    if role in PRIV_STAFF_ROLES + [MANAGEMENT]:
        # Check for a redirect to the feedback list
        feedback_list = reverse("region_feedback", kwargs=region_slug_param)
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
            == f"{settings.LOGIN_URL}?next={mark_region_feedback_as_read}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_mark_region_feedback_as_unread(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # Mark feedback as unread
    mark_region_feedback_as_unread = reverse(
        "mark_region_feedback_as_unread", kwargs=region_slug_param
    )
    test_feedback_id = 6
    response = client.post(
        mark_region_feedback_as_unread, data={"selected_ids[]": [test_feedback_id]}
    )

    if role in PRIV_STAFF_ROLES + [MANAGEMENT]:
        # Check for a redirect to the feedback list
        feedback_list = reverse("region_feedback", kwargs=region_slug_param)
        assert response.status_code == 302
        assert response.headers.get("Location") == feedback_list

        # Check for a success message
        response = client.get(feedback_list)
        assert_message_in_log(
            "SUCCESS  Feedback was successfully marked as unread", caplog
        )

        # Check that feedback has been marked as unread by the user in the database
        feedback = Feedback.objects.get(id=test_feedback_id)
        assert feedback.read_by == None

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={mark_region_feedback_as_unread}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_archive_region_feedback(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # Archive feedback
    archive_region_feedback = reverse(
        "archive_region_feedback", kwargs=region_slug_param
    )
    test_feedback_id = 4
    response = client.post(
        archive_region_feedback, data={"selected_ids[]": [test_feedback_id]}
    )

    if role in PRIV_STAFF_ROLES + [MANAGEMENT]:
        # Check for a redirect to the feedback list
        feedback_list = reverse("region_feedback", kwargs=region_slug_param)
        assert response.status_code == 302
        assert response.headers.get("Location") == feedback_list

        # Check for a success message
        response = client.get(feedback_list)
        assert_message_in_log("SUCCESS  Feedback was successfully archived", caplog)

        # Check that feedback has been archived by the user in the database
        feedback = Feedback.objects.get(id=test_feedback_id)
        assert feedback.archived == True

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_region_feedback}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_restore_region_feedback(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # Restore feedback
    restore_region_feedback = reverse(
        "restore_region_feedback", kwargs=region_slug_param
    )
    test_feedback_id = 5
    response = client.post(
        restore_region_feedback, data={"selected_ids[]": [test_feedback_id]}
    )

    if role in PRIV_STAFF_ROLES + [MANAGEMENT]:
        # Check for a redirect to the feedback list
        feedback_list = reverse("region_feedback_archived", kwargs=region_slug_param)
        assert response.status_code == 302
        assert response.headers.get("Location") == feedback_list

        # Check for a success message
        response = client.get(feedback_list)
        assert_message_in_log("SUCCESS  Feedback was successfully restored", caplog)

        # Check that feedback has been restored by the user in the database
        feedback = Feedback.objects.get(id=test_feedback_id)
        assert feedback.archived == False

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={restore_region_feedback}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_delete_region_feedback(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # delete feedback
    delete_region_feedback = reverse("delete_region_feedback", kwargs=region_slug_param)
    feedback_to_delete_id = 4
    response = client.post(
        delete_region_feedback, data={"selected_ids[]": [feedback_to_delete_id]}
    )

    if role in HIGH_PRIV_STAFF_ROLES + [MANAGEMENT]:
        # Check for a redirect to the feedback list
        feedback_list = reverse("region_feedback", kwargs=region_slug_param)
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
            == f"{settings.LOGIN_URL}?next={delete_region_feedback}"
        )

    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
def test_csv_export_feedback(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    client, role = login_role_user

    csv_export = reverse(
        "export_region_feedback", kwargs={**region_slug_param, "file_format": "csv"}
    )
    csv_to_export_ids = [7, 8]
    response = client.post(csv_export, data={"selected_ids[]": csv_to_export_ids})

    if role in STAFF_ROLES + [MANAGEMENT]:
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/csv"

        csv_content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(csv_content))

        expected_header = [
            "Kategorie",
            "Feedback zu",
            "Sprache",
            "Bewertung",
            "Gelesen von",
            "Kommentar",
            "Datum",
        ]
        assert next(csv_reader) == expected_header

        expected_data_row = [
            "Regionen-Feedback",
            "Augsburg",
            "Deutsch",
            "Positiv",
            "Root User",
            "Read positive feedback CSV export",
            "11.08.2019 07:57",
        ]
        assert next(csv_reader) == expected_data_row

        expected_data_row = [
            "Regionen-Feedback",
            "Augsburg",
            "Deutsch",
            "Negativ",
            "",
            "Unread negative feedback CSV export",
            "11.08.2019 07:57",
        ]
        assert next(csv_reader) == expected_data_row

        with pytest.raises(StopIteration):
            next(csv_reader)

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={csv_export}"
        )

    else:
        assert response.status_code == 403
