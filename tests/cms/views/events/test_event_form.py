from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Event, EventTranslation
from tests.conftest import ANONYMOUS, PRIV_STAFF_ROLES, WRITE_ROLES
from tests.utils import assert_message_in_log

REGION_SLUG = "augsburg"
POI_ID = 4  # Use a POI which belongs to the region with REGION_SLUG
EVENT_TITLE = (
    "New Event"  # Choose a name that does not exist yet as event title in the test data
)


# Possible combinations
# (<ID of selected POI>, <Whether "no physical location" is checked>, <whether successful or not> )
parameters = [
    (-1, False, False),
    (None, True, True),
    (POI_ID, False, True),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", parameters)
def test_create_event(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[int, bool, bool],
) -> None:
    """
    Test that event creation is working as expected (focus on location check)
    """
    client, role = login_role_user
    poi_id, has_not_location, successfully_created = parameter
    settings.LANGUAGE_CODE = "en"

    new_event = reverse(
        "new_event",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": "de",
        },
    )
    data = {
        "title": EVENT_TITLE,
        "content": "Lorem ipsum...",
        "start_date": "2030-01-01",
        "end_date": "2030-01-01",
        "is_all_day": True,
        "status": status.PUBLIC,
    }
    if has_not_location:
        data = copy.deepcopy(data)
        data.update({"has_not_location": True})
    if poi_id:
        data = copy.deepcopy(data)
        data.update({"location": poi_id})
    response = client.post(
        new_event,
        data=data,
    )
    if role in PRIV_STAFF_ROLES + WRITE_ROLES:
        response.status_code == 302

        if successfully_created:
            redirect_url = response.headers.get("location")
            assert_message_in_log(
                f'SUCCESS  Event "{EVENT_TITLE}" was successfully created',
                caplog,
            )
            assert (
                f"Event &quot;{EVENT_TITLE}&quot; was successfully created"
                in client.get(redirect_url).content.decode("utf-8")
            )

            event_translation = EventTranslation.objects.filter(
                title=EVENT_TITLE
            ).first()
            assert event_translation
            assert Event.objects.filter(id=event_translation.event.id).first()

        else:
            assert_message_in_log(
                "ERROR    Location: Either disable the event location or provide a valid location",
                caplog,
            )
            assert (
                "Either disable the event location or provide a valid location"
                in response.content.decode("utf-8")
            )

            event_translation = EventTranslation.objects.filter(
                title=EVENT_TITLE
            ).first()
            assert not event_translation

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={new_event}"
        )
    else:
        assert response.status_code == 403
