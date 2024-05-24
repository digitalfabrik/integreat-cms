import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models.events.external_calendar import ExternalCalendar

from tests.conftest import ANONYMOUS, CMS_TEAM, ROOT, SERVICE_TEAM


@pytest.mark.django_db
def test_permissions_for_imported_events_list(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    imported_events_view = reverse(
        "external_calendar_list",
        kwargs={"region_slug": "augsburg"},
    )
    response = client.get(imported_events_view)

    if role in [CMS_TEAM, ROOT, SERVICE_TEAM]:
        assert response.status_code == 200
        assert "Externen Kalender importieren" in response.content.decode("utf-8")
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={imported_events_view}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.parametrize(
    "login_role_user", [CMS_TEAM, SERVICE_TEAM, ROOT], indirect=True
)
@pytest.mark.django_db
def test_imported_events_lists_shows_expected_events(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    number_of_expected_external_calendars = 0
    number_of_external_calendars = ExternalCalendar.objects.count()
    assert number_of_expected_external_calendars == number_of_external_calendars


@pytest.mark.django_db
def test_creating_imported_event_works(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:

    assert False


# test_editing_imported_event_works():

# test_deleting_imported_event_works():
