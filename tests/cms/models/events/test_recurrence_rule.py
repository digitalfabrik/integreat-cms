"""
Test module for RecurrenceRule class
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from integreat_cms.cms.constants import weekdays, weeks
from integreat_cms.cms.models import Event, RecurrenceRule

if TYPE_CHECKING:
    from rrule import rrule


class TestCreatingIcalRule:
    """
    Test whether to_ical_rrule_string function is calculating the rrule correctly
    """

    test_event = Event(
        start=datetime.datetime(2030, 1, 1, 11, 30, 0, 0, ZoneInfo("UTC")),
        end=datetime.datetime(2030, 1, 1, 12, 30, 0, 0, ZoneInfo("UTC")),
    )

    def test_api_rrule_every_year_start_date_in_the_past(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="YEARLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=None,
            week_for_monthly=None,
            recurrence_end_date=None,
        )
        test_event = Event(
            start=datetime.datetime(2020, 1, 1, 11, 30, 0, 0, ZoneInfo("UTC")),
            end=datetime.datetime(2030, 1, 1, 12, 30, 0, 0, ZoneInfo("UTC")),
        )
        test_event.recurrence_rule = recurrence_rule
        ical_rrule = recurrence_rule.to_ical_rrule_string()
        assert ical_rrule == "DTSTART:20200101T113000\nRRULE:FREQ=YEARLY"

    def check_rrule(self, recurrence_rule: rrule, expected: str) -> None:
        self.test_event.recurrence_rule = recurrence_rule
        ical_rrule = recurrence_rule.to_ical_rrule_string()
        assert ical_rrule == expected

    def test_api_rrule_every_three_days(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="DAILY",
            interval=3,
            weekdays_for_weekly=None,
            weekday_for_monthly=None,
            week_for_monthly=None,
            recurrence_end_date=None,
        )
        self.check_rrule(
            recurrence_rule,
            "DTSTART:20300101T113000\nRRULE:FREQ=DAILY;INTERVAL=3",
        )

    def test_api_rrule_weekly(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="WEEKLY",
            interval=1,
            weekdays_for_weekly=[weekdays.MONDAY, weekdays.TUESDAY],
            weekday_for_monthly=None,
            week_for_monthly=None,
            recurrence_end_date=None,
        )
        self.check_rrule(
            recurrence_rule,
            "DTSTART:20300101T113000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU",
        )

    def test_api_rrule_monthly(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="MONTHLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=weekdays.FRIDAY,
            week_for_monthly=weeks.FIRST,
            recurrence_end_date=None,
        )
        self.check_rrule(
            recurrence_rule,
            "DTSTART:20300101T113000\nRRULE:FREQ=MONTHLY;BYDAY=+1FR",
        )

    def test_api_rrule_last_week_in_month(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="MONTHLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=weekdays.WEDNESDAY,
            week_for_monthly=weeks.LAST,
            recurrence_end_date=None,
        )
        self.check_rrule(
            recurrence_rule,
            "DTSTART:20300101T113000\nRRULE:FREQ=MONTHLY;BYDAY=-1WE",
        )

    def test_api_rrule_bimonthly_until(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="MONTHLY",
            interval=2,
            weekdays_for_weekly=None,
            weekday_for_monthly=weekdays.SUNDAY,
            week_for_monthly=weeks.FIRST,
            recurrence_end_date=datetime.date(2030, 10, 19),
        )
        self.check_rrule(
            recurrence_rule,
            "DTSTART:20300101T113000\nRRULE:FREQ=MONTHLY;INTERVAL=2;UNTIL=20301019T235959;BYDAY=+1SU",
        )

    def test_api_rrule_yearly(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="YEARLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=None,
            week_for_monthly=None,
            recurrence_end_date=None,
        )
        self.check_rrule(recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=YEARLY")
