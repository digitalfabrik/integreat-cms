import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from tests.conftest import ANONYMOUS


@pytest.mark.django_db
def test_barrier_free_and_organization_box_appear(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    barrier_free_box = '<div id="poi-barrier-free"'
    organization_box = '<div id="poi-organization"'
    client, role = login_role_user

    edit_poi = reverse(
        "edit_poi",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "poi_id": 1},
    )
    response = client.get(edit_poi)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={edit_poi}"
        )
        return

    assert organization_box in response.content.decode("utf-8")
    assert barrier_free_box in response.content.decode("utf-8")
