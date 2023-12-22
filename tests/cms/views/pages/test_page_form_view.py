from typing import TYPE_CHECKING

import pytest
from django.test.client import Client
from django.urls import reverse

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


@pytest.mark.django_db
def test_display_page_form(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client, role = login_role_user

    # delete feedback
    get_welcome_page_form = reverse(
        "edit_page",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "page_id": 1},
    )
    response = client.get(get_welcome_page_form)

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
