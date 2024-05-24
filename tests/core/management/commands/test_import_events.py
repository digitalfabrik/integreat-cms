from __future__ import annotations

import pytest
from pytest_httpserver import HTTPServer

from integreat_cms.cms.models import Event, EventTranslation, ExternalCalendar, Region

from ..utils import get_command_output

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
CALENDARS = [
    (CALENDAR_V1, [CALENDAR_V1_EVENT_NAME]),
    (CALENDAR_v2, [CALENDAR_V2_EVENT_NAME]),
    (CALENDAR_EMPTY, []),
    (CALENDAR_WRONG_CATEGORY, [CALENDAR_WRONG_CATEGORY_EVENT_NAME]),
]


def serve(server: HTTPServer, file: str) -> str:
    """
    Serves the given file from
    :param server: The server
    :param file: The file to serve
    :return: The url of the served file
    """
    with open(file, "r") as f:
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
        region=region, url=url, name="Test Calendar", import_filter_tag=""
    )
    calendar.save()
    return calendar


@pytest.mark.django_db
def test_import_without_calendars() -> None:
    """
    Tests that the import command does not fail if no external calendars are configured
    """
    out, err = get_command_output("import_events")
    assert not err


@pytest.mark.parametrize("calendar_data", CALENDARS)
@pytest.mark.django_db
def test_import_successful(
    httpserver: HTTPServer, load_test_data: None, calendar_data: tuple[str, list[str]]
) -> None:
    """
    Tests that the calendars in the test data can be imported correctly
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param calendar_data: A tuple of calendar path and event names of this calendar
    """
    calendar_file, event_names = calendar_data
    calendar_url = serve(httpserver, calendar_file)
    calendar = setup_calendar(calendar_url)

    assert not EventTranslation.objects.filter(
        event__region=calendar.region, title__in=event_names
    ).exists(), "Event should not exist before import"

    out, err = get_command_output("import_events")
    assert not err

    assert all(
        EventTranslation.objects.filter(
            event__region=calendar.region, title=title
        ).exists()
        for title in event_names
    ), "Events should exist after import"


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
        event__region=calendar.region, title=CALENDAR_V1_EVENT_NAME
    ).first()
    assert event_translation is not None, "Event should exist after import"

    serve(httpserver, CALENDAR_v2)
    out, err = get_command_output("import_events")
    assert not err
    assert "Imported event" in out

    assert (
        event_translation.latest_version.title == CALENDAR_V2_EVENT_NAME
    ), "event should be renamed"


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
        event__region=calendar.region, title=CALENDAR_V1_EVENT_NAME
    ).first()
    assert event_translation is not None, "Event should exist after import"

    serve(httpserver, CALENDAR_EMPTY)
    out, err = get_command_output("import_events")
    assert not err
    assert "Deleting 1 unused events: " in out

    assert not EventTranslation.objects.filter(
        slug=event_translation.slug
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

    out, err = get_command_output("import_events")
    assert "Could not import event because it does not have a required field: " in err


@pytest.mark.django_db
def test_import_event_without_tags(
    httpserver: HTTPServer, load_test_data: None
) -> None:
    """
    Tests that an event does not get imported if it does not have tags, but tags are required
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_V1)
    calendar = setup_calendar(calendar_url)

    calendar.import_filter_tag = "integreat"
    calendar.save()

    out, err = get_command_output("import_events")
    assert not err
    assert f"Skipping event {CALENDAR_V1_EVENT_NAME} without tags" in out


@pytest.mark.django_db
def test_import_event_with_wrong_tag(
    httpserver: HTTPServer, load_test_data: None
) -> None:
    """
    Tests that an event does not get imported if it does not have the right tag
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_WRONG_CATEGORY)
    calendar = setup_calendar(calendar_url)

    calendar.import_filter_tag = "integreat"
    calendar.save()

    out, err = get_command_output("import_events")
    assert not err
    assert (
        f"Skipping event {CALENDAR_WRONG_CATEGORY_EVENT_NAME} with tags: {CALENDAR_WRONG_CATEGORY_TAG}"
        in out
    )


@pytest.mark.django_db
def test_import_event_with_correct_tag(
    httpserver: HTTPServer, load_test_data: None
) -> None:
    """
    Tests that an event gets imported if it has the right tag
    :param httpserver: The server
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    calendar_url = serve(httpserver, CALENDAR_WRONG_CATEGORY)
    calendar = setup_calendar(calendar_url)

    calendar.import_filter_tag = CALENDAR_WRONG_CATEGORY_TAG
    calendar.save()

    assert not EventTranslation.objects.filter(
        event__region=calendar.region, title=CALENDAR_WRONG_CATEGORY_EVENT_NAME
    ).exists(), "Event should not exist before import"

    out, err = get_command_output("import_events")
    assert not err
    assert "Imported event" in out

    assert EventTranslation.objects.filter(
        event__region=calendar.region, title=CALENDAR_WRONG_CATEGORY_EVENT_NAME
    ).exists(), "Event should exist after import"
