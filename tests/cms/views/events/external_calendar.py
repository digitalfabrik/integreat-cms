import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import ExternalCalendar
from tests.conftest import ANONYMOUS, CMS_TEAM, ROOT, SERVICE_TEAM


@pytest.mark.django_db
def test_permissions_for_external_calendar_list(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    external_calendars_list = reverse(
        "external_calendar_list",
        kwargs={"region_slug": "augsburg"},
    )
    response = client.get(external_calendars_list)

    if role in [CMS_TEAM, ROOT, SERVICE_TEAM]:
        assert response.status_code == 200
        assert "Externe Kalender" in response.content.decode("utf-8")
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={external_calendars_list}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_permissions_for_creating_new_external_calendar(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    new_external_calendar = reverse(
        "new_external_calendar",
        kwargs={"region_slug": "augsburg"},
    )
    response = client.get(new_external_calendar)

    if role in [CMS_TEAM, ROOT, SERVICE_TEAM]:
        assert response.status_code == 200
        assert "Neuen externen Kalender hinzufügen" in response.content.decode("utf-8")
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_external_calendar}"
        )
    else:
        assert response.status_code == 403
