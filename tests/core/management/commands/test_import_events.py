from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from integreat_cms.cms.models import (
    EventTranslation,
    ExternalCalendar,
    RecurrenceRule,
    Region,
)

from ..utils import get_command_output

if TYPE_CHECKING:
    from pytest_httpserver import HTTPServer

CALENDAR_V1_EVENT_NAME = "Testevent"
CALENDAR_V1 = "tests/core/management/commands/assets/calendars/single_event.ics"
CALENDAR_V2_EVENT_NAME = "Testeventv2"
CALENDAR_v2 = "tests/core/management/commands/assets/calendars/single_event_v2.ics"
CALENDAR_EMPTY = "tests/core/management/commands/assets/calendars/empty_calendar.ics"
CALENDAR_WRONG_CATEGORY = (
    "tests/core/management/commands/assets/calendars/event_with_wrong_category.ics"
)
CALENDAR_WRONG_CATEGORY_EVENT_NAME = "wrong_category"
CALENDAR_WRONG_CATEGORY_TAG = "private"
CALENDAR_CORRUPTED = (
    "tests/core/management/commands/assets/calendars/corrupted_event.ics"
)
CALENDAR_MULTIPLE_CATEGORIES = (
    "tests/core/management/commands/assets/calendars/event_with_multiple_categories.ics"
)
CALENDAR_RECURRENCE_RULES = (
    "tests/core/management/commands/assets/calendars/recurrence_rules.ics"
)
CALENDAR_OUTLOOK = (
    "tests/core/management/commands/assets/calendars/outlook_calendar.ics"
)
CALENDAR_DAILY_EVENT = (
    "tests/core/management/commands/assets/calendars/event_with_daily_recurrence.ics"
)
CALENDAR_SINGLE_RECURRING_EVENT_A = (
    "tests/core/management/commands/assets/calendars/single_recurring_event_a.ics"
)
CALENDAR_SINGLE_RECURRING_EVENT_B = (
    "tests/core/management/commands/assets/calendars/single_recurring_event_b.ics"
)

#: A Collection of (Calendar file, events in that file, recurrence rules in that file)
CALENDARS = [
    (CALENDAR_V1, [CALENDAR_V1_EVENT_NAME], {}),
    (CALENDAR_v2, [CALENDAR_V2_EVENT_NAME], {}),
    (CALENDAR_EMPTY, [], {}),
    (CALENDAR_WRONG_CATEGORY, [CALENDAR_WRONG_CATEGORY_EVENT_NAME], {}),
    (
        CALENDAR_RECURRENCE_RULES,
        [
            "Singular event",
            "Every first Monday",
            "Weekly event",
            "Every year until 2034",
            "Every 3rd Wednesday",
        ],
        {
            "DTSTART:20241112T230000\nRRULE:FREQ=MONTHLY;BYDAY=+1MO",
            "DTSTART:20241113T190000\nRRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR",
            "DTSTART:20241112T230000\nRRULE:FREQ=YEARLY;UNTIL=20341112T235959",
            "DTSTART:20241112T230000\nRRULE:FREQ=MONTHLY;BYDAY=+3WE",
        },
    ),
    (
        CALENDAR_OUTLOOK,
        ["Weekly - On Wednesday only - Never ends", "Yearly - End after 2 times"],
        {
            "DTSTART:20241231T230000\nRRULE:FREQ=WEEKLY;UNTIL=20250513T235959;BYDAY=WE",
            "DTSTART:20241231T230000\nRRULE:FREQ=YEARLY;UNTIL=20271231T235959",
        },
    ),
    (CALENDAR_SINGLE_RECURRING_EVENT_B, ["Repeating event?"], {}),
]


def serve(server: HTTPServer, file: str) -> str:
    """
    Serves the given file
    :param server: The server
    :param file: The file to serve
    :return: The url of the served file
    """
    with open(file, encoding="utf-8") as f:
        server.expect_oneshot_request("/get_calendar").respond_with_data(f.read())
    return server.url_for("/get_calendar")


def setup_calendar(url: str) -> ExternalCalendar:
    """
    Creates a Calendar instance
    :param url: The url of the external calendar
    :return: An External Calendar object
    """
    region = Region.objects.get(slug="testumgebung")
    calendar = ExternalCalendar.objects.create(
        region=region,
        url=url,
        name="Test Calendar",
        import_filter_category="",
    )
    calendar.save()
    return calendar


@pytest.mark.django_db
def test_import_without_calendars() -> None:
    """
    Tests that the import command does not fail if no external calendars are configured
    """
    _, err = get_command_output("import_events")
    assert not err


@pytest.mark.parametrize("calendar_data", CALENDARS)
@pytest.mark.django_db
def test_import_successful(
    httpserver: HTTPServer,
    load_test_data: None,
    calendar_data: tuple[str, list[str], set[str]],
) -> None:
    """
    Tests that the calendars in the test data can be imported correctly
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param calendar_data: A tuple of calendar path and event names of this calendar
    """
    calendar_file, event_names, recurrence_rules = calendar_data
    calendar_url = serve(httpserver, calendar_file)
    calendar = setup_calendar(calendar_url)

    assert not EventTranslation.objects.filter(
        event__region=calendar.region,
        title__in=event_names,
    ).exists(), "Event should not exist before import"

    for rule in RecurrenceRule.objects.all():
        assert rule.to_ical_rrule_string() not in recurrence_rules, (
            "Recurrence rule should not exist before import"
        )

    _, err = get_command_output("import_events")
    assert not err

    assert all(
        EventTranslation.objects.filter(
            event__region=calendar.region,
            title=title,
        ).exists()
        for title in event_names
    ), "Events should exist after import"

    new_rules = {rule.to_ical_rrule_string() for rule in RecurrenceRule.objects.all()}
    print(new_rules)
    for rule in recurrence_rules:
        assert rule in new_rules, "Recurrence rule should exist after import"


@pytest.mark.django_db
def test_update_event(httpserver: HTTPServer, load_test_data: None) -> None:
    """
    Tests that an event gets updated if it is updated in the ical file
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_V1)
    calendar = setup_calendar(calendar_url)

    out, err = get_command_output("import_events")
    assert not err
    assert "Imported event" in out

    event_translation = EventTranslation.objects.filter(
        event__region=calendar.region,
        title=CALENDAR_V1_EVENT_NAME,
    ).first()
    assert event_translation is not None, "Event should exist after import"

    serve(httpserver, CALENDAR_v2)
    out, err = get_command_output("import_events")
    assert not err
    assert "Imported event" in out

    assert event_translation.latest_version.title == CALENDAR_V2_EVENT_NAME, (
        "event should be renamed"
    )


@pytest.mark.django_db
def test_delete_event(httpserver: HTTPServer, load_test_data: None) -> None:
    """
    Tests that an event gets deleted if it is deleted in the ical file
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_V1)
    calendar = setup_calendar(calendar_url)

    out, err = get_command_output("import_events")
    assert not err

    event_translation = EventTranslation.objects.filter(
        event__region=calendar.region,
        title=CALENDAR_V1_EVENT_NAME,
    ).first()
    assert event_translation is not None, "Event should exist after import"

    serve(httpserver, CALENDAR_EMPTY)
    out, err = get_command_output("import_events")
    assert not err
    assert "Deleting 1 unused events: " in out

    assert not EventTranslation.objects.filter(
        slug=event_translation.slug,
    ).exists(), "Event should be deleted"


@pytest.mark.django_db
def test_import_corrupted_event(httpserver: HTTPServer, load_test_data: None) -> None:
    """
    Tests that an invalid event gets handled correctly and does not cause the command to crash
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_CORRUPTED)
    setup_calendar(calendar_url)

    _, err = get_command_output("import_events")
    assert "Could not import event because it does not have a required field: " in err


@pytest.mark.django_db
def test_import_event_without_tags(
    httpserver: HTTPServer,
    load_test_data: None,
) -> None:
    """
    Tests that an event does not get imported if it does not have tags, but tags are required
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_V1)
    calendar = setup_calendar(calendar_url)

    calendar.import_filter_category = "integreat"
    calendar.save()

    out, err = get_command_output("import_events")
    assert not err
    assert f"Skipping event {CALENDAR_V1_EVENT_NAME} with tags: []" in out


@pytest.mark.django_db
def test_import_event_with_wrong_tag(
    httpserver: HTTPServer,
    load_test_data: None,
) -> None:
    """
    Tests that an event does not get imported if it does not have the right tag
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_WRONG_CATEGORY)
    calendar = setup_calendar(calendar_url)

    calendar.import_filter_category = "integreat"
    calendar.save()

    out, err = get_command_output("import_events")
    assert not err
    assert (
        f"Skipping event {CALENDAR_WRONG_CATEGORY_EVENT_NAME} with tags: [{CALENDAR_WRONG_CATEGORY_TAG}]"
        in out
    )


@pytest.mark.django_db
def test_import_event_with_correct_tag(
    httpserver: HTTPServer,
    load_test_data: None,
) -> None:
    """
    Tests that an event gets imported if it has the right tag
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_WRONG_CATEGORY)
    calendar = setup_calendar(calendar_url)

    calendar.import_filter_category = CALENDAR_WRONG_CATEGORY_TAG
    calendar.save()

    assert not EventTranslation.objects.filter(
        event__region=calendar.region,
        title=CALENDAR_WRONG_CATEGORY_EVENT_NAME,
    ).exists(), "Event should not exist before import"

    out, err = get_command_output("import_events")
    assert not err
    assert "Imported event" in out

    assert EventTranslation.objects.filter(
        event__region=calendar.region,
        title=CALENDAR_WRONG_CATEGORY_EVENT_NAME,
    ).exists(), "Event should exist after import"


@pytest.mark.django_db
def test_import_event_with_multiple_categories(
    httpserver: HTTPServer,
    load_test_data: None,
) -> None:
    """
    Tests that an event does not get imported if it has multiple category definitions
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_MULTIPLE_CATEGORIES)
    setup_calendar(calendar_url)

    out, err = get_command_output("import_events")
    print(err)
    assert not err
    assert "Imported event" in out


@pytest.mark.django_db
def test_import_and_remove_recurrence_rule(
    httpserver: HTTPServer,
    load_test_data: None,
) -> None:
    """
    Imports an event with a recurrence rule and later the same event without recurrence rule.
    Tests that the recurrence rule gets deleted when it is not needed anymore after the second import.
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_SINGLE_RECURRING_EVENT_A)
    calendar = setup_calendar(calendar_url)

    _, err = get_command_output("import_events")
    assert not err

    assert RecurrenceRule.objects.filter(
        event__external_calendar=calendar,
    ).exists(), "The recurrence rule should exist after import"
    event = calendar.events.first()
    assert event, "Event should have been created"

    # Now, import the updated calendar where the recurrence rule was removed
    serve(httpserver, CALENDAR_SINGLE_RECURRING_EVENT_B)
    _, err = get_command_output("import_events")
    assert not err

    assert not RecurrenceRule.objects.filter(
        event__external_calendar=calendar,
    ).exists(), "The recurrence rule should not exist anymore after update"
    new_event = calendar.events.first()
    assert event.id == new_event.id, "The event should still exist"


@pytest.mark.django_db
def test_daily_event_not_imported(httpserver: HTTPServer, load_test_data: None) -> None:
    """
    Tests that an event with daily recurrence is not imported
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """

    calendar_url = serve(httpserver, CALENDAR_DAILY_EVENT)
    calendar = setup_calendar(calendar_url)

    _, err = get_command_output("import_events")

    assert not RecurrenceRule.objects.filter(
        event__external_calendar=calendar
    ).exists(), "The recurrence rule should not exist"
    assert not calendar.events.exists(), "The event should not exist"

    assert "Could not import event" in err
