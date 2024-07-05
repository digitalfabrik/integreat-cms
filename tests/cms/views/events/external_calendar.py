import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import resolve, reverse

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


@pytest.mark.django_db
def test_creating_new_external_calendar(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    new_external_calendar = reverse(
        "new_external_calendar",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.post(
        new_external_calendar,
        data={
            "name": "Test external calendar",
            "url": "https://integreat.app/",
            "import_filter_category": "integreat",
        },
    )

    if role in [CMS_TEAM, ROOT, SERVICE_TEAM]:
        assert response.status_code == 302, "We should be redirected to the edit view"

        edit_url = response.headers.get("location")
        url_params = resolve(edit_url)
        assert (
            url_params.url_name == "edit_external_calendar"
        ), "We should be redirected to the edit view"
        assert (
            url_params.kwargs["region_slug"] == "augsburg"
        ), "The region shouldn't be different from the request"
        id_of_external_calendar = url_params.kwargs["calendar_id"]

        external_calendar = ExternalCalendar.objects.get(id=id_of_external_calendar)
        assert (
            external_calendar.name == "Test external calendar"
        ), "Name should be successfully set on the model"
        assert (
            external_calendar.url == "https://integreat.app/"
        ), "URL should be successfully set on the model"
        assert (
            external_calendar.import_filter_category == "integreat"
        ), "Filter category should be successfully set on the model"
    elif role == ANONYMOUS:
        assert response.status_code == 302, "We should be redirected to the login view"
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_external_calendar}"
        )
    else:
        assert response.status_code == 403
