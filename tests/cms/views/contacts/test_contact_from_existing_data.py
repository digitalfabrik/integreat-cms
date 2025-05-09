import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from tests.conftest import ANONYMOUS


@pytest.mark.django_db
def test_suggest_contacts_is_shown(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    get_potential_targets = reverse(
        "potential_targets",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(get_potential_targets)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={get_potential_targets}"
        )
        return

    assert response.status_code == 200
    assert "Potential contact data" in response.content.decode("utf-8")
