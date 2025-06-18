from __future__ import annotations

import copy
from datetime import timedelta
from typing import TYPE_CHECKING

from django.utils.timezone import now

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.contrib.auth import get_user_model
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone

from integreat_cms.cms.constants import frequency, status
from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Language,
    RecurrenceRule,
    Region,
)
from tests.cms.views.bulk_actions import assert_bulk_delete, BulkActionIDs
from tests.conftest import ANONYMOUS, PRIV_STAFF_ROLES, WRITE_ROLES
from tests.utils import assert_message_in_log

REGION_SLUG = "augsburg"
POI_ID = 4  # Use a POI which belongs to the region with REGION_SLUG
EVENT_TITLE = (
    "New Event"  # Choose a name that does not exist yet as event title in the test data
)


# Possible combinations
# (<ID of selected POI>, <Whether "no physical location" is checked>, <whether successful or not> )
location_test_parameters = [
    (-1, False, False),
    (None, True, True),
    (POI_ID, False, True),
]


def create_event(region_slug: str, name_add: str = "") -> int:
    """
    A helper function to create a new POI that is unused (and therefore deletable)

    Returns the new events ID
    """

    start_time = now()
    end_time = start_time + timedelta(hours=1)

    region = Region.objects.get(slug=region_slug)
    language = Language.objects.get(slug="en")

    event = Event.objects.create(
        region=region,
        start=start_time,
        end=end_time,
        archived=False,
    )

    EventTranslation.objects.create(
        event=event,
        language=language,
        title=f"Test Event{name_add}",
        slug=f"test-event{name_add}".lower(),
    )

    return event.id


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", location_test_parameters)
def test_create_event_location_check(
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
        assert response.status_code in [200, 302]
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
                title=EVENT_TITLE,
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
                title=EVENT_TITLE,
            ).first()
            assert not event_translation

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={new_event}"
        )
    else:
        assert response.status_code == 403


# (<event title>, <end date>, <whether the event is recurring>)
event_creation_test_parameters = [
    ("One time event", None, False),
    ("Recurring event", None, True),
    ("Long term event", "2030-12-31", False),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", event_creation_test_parameters)
def test_create_event(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[str, str, bool],
) -> None:
    """
    Test that an event is created as expected
    """
    client, role = login_role_user
    event_title, end_date, is_recurring = parameter
    settings.LANGUAGE_CODE = "en"

    new_event = reverse(
        "new_event",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": "de",
        },
    )
    data = {
        "title": event_title,
        "content": "Lorem ipsum...",
        "start_date": "2030-01-01",
        "is_all_day": True,
        "status": status.PUBLIC,
    }
    if end_date:
        data = copy.deepcopy(data)
        data.update(
            {
                "end_date": end_date,
                "is_long_term": True,
            }
        )
    else:
        data = copy.deepcopy(data)
        data.update(
            {
                "is_long_term": False,
            }
        )
    if is_recurring:
        data = copy.deepcopy(data)
        data.update(
            {
                "is_recurring": is_recurring,
                "frequency": frequency.WEEKLY,
                "interval": 1,
                "weekdays_for_weekly": [1],
            }
        )
    response = client.post(
        new_event,
        data=data,
    )

    if role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert response.status_code == 302

        redirect_url = response.headers.get("location")
        assert_message_in_log(
            f'SUCCESS  Event "{event_title}" was successfully created',
            caplog,
        )
        assert (
            f"Event &quot;{event_title}&quot; was successfully created"
            in client.get(redirect_url).content.decode("utf-8")
        )

        event = EventTranslation.objects.filter(title=event_title).first().event
        if end_date:
            assert timezone.localtime(event.end).date().strftime("%Y-%m-%d") == end_date
        else:
            assert (
                timezone.localtime(event.start).date()
                == timezone.localtime(event.end).date()
            )
        if is_recurring:
            assert event.recurrence_rule
        else:
            assert not event.recurrence_rule

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={new_event}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_no_daily_event_created(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test that no event with daily recurrence is created
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    new_event = reverse(
        "new_event",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": "de",
        },
    )
    data = {
        "title": "Forbidden recurrence",
        "content": "Lorem ipsum...",
        "start_date": "2030-01-01",
        "is_all_day": True,
        "status": status.PUBLIC,
        "is_recurring": True,
        "is_long_term": False,
        "frequency": frequency.DAILY,
        "interval": 1,
        "weekdays_for_weekly": [1],
    }
    response = client.post(
        new_event,
        data=data,
    )

    if role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert response.status_code == 200

        assert_message_in_log(
            'ERROR    Frequency: Recurrence "daily" is not allowed anymore',
            caplog,
        )
        assert (
            "Recurrence &quot;daily&quot; is not allowed anymore"
            in response.content.decode("utf-8")
        )

        assert not EventTranslation.objects.filter(title="Forbidden recurrence").first()

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={new_event}"
        )
    else:
        assert response.status_code == 403


recurrence_rule_change_parameters = [None, "2030-12-31"]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", recurrence_rule_change_parameters)
def test_no_orpahned_recurrence_rule(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: str | None,
) -> None:
    """
    Test that the recurrence rule is deleted and the end date is correctly modified when a recurring event is changed to an one-time event or long-term event
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    recurring_event = (
        Event.objects.filter(region__slug=REGION_SLUG)
        .exclude(recurrence_rule=None)
        .first()
    )
    assert recurring_event
    recurring_event_id = recurring_event.id
    recurrence_rule_id = recurring_event.recurrence_rule.id

    new_event = reverse(
        "edit_event",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": "de",
            "event_id": recurring_event_id,
        },
    )
    data = {
        "title": "I was recurring",
        "content": "Lorem ipsum...",
        "start_date": "2030-01-01",
        "is_all_day": True,
        "status": status.PUBLIC,
        "frequency": frequency.DAILY,
        "interval": 1,
        "weekdays_for_weekly": [1],
    }
    if parameter:
        data = copy.deepcopy(data)
        data.update(
            {
                "is_long_term": True,
                "end_date": parameter,
            }
        )
    else:
        data = copy.deepcopy(data)
        data.update(
            {
                "is_recurring": False,
                "is_long_term": False,
            }
        )
    response = client.post(
        new_event,
        data=data,
    )

    if role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert response.status_code == 302

        redirect_url = response.headers.get("location")
        assert_message_in_log(
            'SUCCESS  Event "I was recurring" was successfully updated',
            caplog,
        )
        assert (
            "Event &quot;I was recurring&quot; was successfully updated"
            in client.get(redirect_url).content.decode("utf-8")
        )

        event = Event.objects.filter(id=recurring_event_id).first()
        assert not event.recurrence_rule
        assert not RecurrenceRule.objects.filter(id=recurrence_rule_id).first()

        if parameter:
            assert (
                timezone.localtime(event.end).date().strftime("%Y-%m-%d") == parameter
            )
        else:
            assert (
                timezone.localtime(event.start).date()
                == timezone.localtime(event.end).date()
            )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={new_event}"
        )
    else:
        assert response.status_code == 403


end_date_change_parameters = [True, False]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", end_date_change_parameters)
def test_end_date_changed(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: bool,
) -> None:
    """
    Test that the end date is correctly modified when a long-term event is changed to an one-time event or recurring event
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    long_term_event = Event.objects.filter(
        ~Q(start__date=F("end__date")),
        region__slug=REGION_SLUG,
        recurrence_rule__isnull=True,
    ).first()
    assert (
        timezone.localtime(long_term_event.start).date()
        != timezone.localtime(long_term_event.end).date()
    )

    long_term_event_id = long_term_event.id

    new_event = reverse(
        "edit_event",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": "de",
            "event_id": long_term_event_id,
        },
    )
    data = {
        "title": "I was long-term",
        "content": "Lorem ipsum...",
        "start_date": long_term_event.start.date(),
        "end_date": long_term_event.end.date(),
        "is_all_day": True,
        "status": status.PUBLIC,
        "is_long_term": False,
    }
    if parameter:
        data = copy.deepcopy(data)
        data.update(
            {
                "is_recurring": True,
                "frequency": frequency.WEEKLY,
                "interval": 1,
                "weekdays_for_weekly": [1],
            }
        )

    response = client.post(
        new_event,
        data=data,
    )

    if role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert response.status_code in [200, 302]

        redirect_url = response.headers.get("location")
        assert_message_in_log(
            'SUCCESS  Event "I was long-term" was successfully updated',
            caplog,
        )
        assert (
            "Event &quot;I was long-term&quot; was successfully updated"
            in client.get(redirect_url).content.decode("utf-8")
        )

        event = Event.objects.filter(id=long_term_event_id).first()
        assert (
            timezone.localtime(event.start).date()
            == timezone.localtime(event.end).date()
        )

        if parameter:
            assert event.recurrence_rule

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={new_event}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ROOT", "AUTHOR"])
@pytest.mark.parametrize(
    "num_deletable, num_undeletable",
    [
        pytest.param(1, 0, id="deletable_event=1"),
        pytest.param(2, 0, id="deletable_events=2"),
    ],
)
def test_bulk_delete_events(
    role: str,
    client: Client,
    load_test_data: None,
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    num_deletable: int,
    num_undeletable: int,
) -> None:
    """
    Test whether bulk deleting of pois works as expected
    """
    user = get_user_model().objects.get(username=role.lower())
    client.force_login(user)

    deletable_events = [create_event("augsburg", f"-{i}") for i in range(num_deletable)]

    instance_ids: BulkActionIDs = {"deletable": deletable_events, "undeletable": [[]]}
    fail_reason = ""
    url = reverse(
        "delete_multiple_events",
        kwargs={"region_slug": "augsburg", "language_slug": "en"},
    )
    assert_bulk_delete(
        Event, instance_ids, url, (client, role), caplog, settings, [fail_reason]
    )
