import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from tests.conftest import (
    ANONYMOUS,
)

data = [
    ("Wöchentlich wiederholende Veranstaltung", "?recurring=1"),
    ("Einmalige Veranstaltung", "?recurring=2"),
    ("Dauerveranstaltung", "?recurring=3"),
]


@pytest.mark.django_db
def test_filtering_by_single_selected_recurrence_is_successful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    get_event_list = reverse(
        "events",
        kwargs={"region_slug": "augsburg"},
    )

    for item in data:
        title, query = item
        url = get_event_list + query
        response = client.get(url)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={get_event_list}"
        )

    else:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        response = client.get(redirect_url)
        print(response)
        assert response.status_code == 200
        assert title in response.content.decode("utf-8")
