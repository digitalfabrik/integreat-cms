"""
Test module for RecurrenceRule class
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import pytest

from integreat_cms.cms.constants import weekdays, weeks
from integreat_cms.cms.models import Event, RecurrenceRule

if TYPE_CHECKING:
    from datetime import date
    from typing import Iterable

    from rrule import rrule


class TestCreatingIcalRule:
    """
    Test whether :fun:`~integreat_cms.cms.models.events.recurrence_rule.RecurrenceRule.to_ical_rrule_string` function is calculating the rrule correctly
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
            recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=DAILY;INTERVAL=3"
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
            recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU"
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
            recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=MONTHLY;BYDAY=+1FR"
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
            recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=MONTHLY;BYDAY=-1WE"
        )

    def test_api_rrule_second_last_week_in_month(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="MONTHLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=weekdays.WEDNESDAY,
            week_for_monthly=weeks.SECOND_LAST,
            recurrence_end_date=None,
        )
        self.check_rrule(
            recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=MONTHLY;BYDAY=-2WE"
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


class TestGeneratingEventsInPython:
    """
    Test whether :fun:`~integreat_cms.cms.models.events.recurrence_rule.RecurrenceRule.iter_after` is generating event instances correctly
    """

    test_event = Event(
        start=datetime.datetime(2030, 1, 1, 11, 30, 0, 0, ZoneInfo("UTC")),
        end=datetime.datetime(2030, 1, 1, 12, 30, 0, 0, ZoneInfo("UTC")),
    )

    def expect_first_items_start(
        self,
        recurrence_rule: RecurrenceRule,
        start_times: Iterable[date],
        event: Event | None = None,
    ) -> None:
        if event is None:
            event = self.test_event
        event.recurrence_rule = recurrence_rule
        gen = recurrence_rule.iter_after(event.start.date())
        for start_time in start_times:
            assert next(gen) == start_time

    def expect_finite_items_start(
        self,
        recurrence_rule: RecurrenceRule,
        start_times: Iterable[date],
        event: Event | None = None,
    ) -> None:
        if event is None:
            event = self.test_event
        event.recurrence_rule = recurrence_rule
        gen = recurrence_rule.iter_after(event.start.date())
        for start_time in start_times:
            assert next(gen) == start_time
        with pytest.raises(StopIteration):
            assert next(gen) is None

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
        self.expect_first_items_start(
            recurrence_rule,
            [
                datetime.date(2020, 1, 1),
                datetime.date(2021, 1, 1),
                datetime.date(2022, 1, 1),
                datetime.date(2023, 1, 1),
                datetime.date(2024, 1, 1),
                datetime.date(2025, 1, 1),
                datetime.date(2026, 1, 1),
                datetime.date(2027, 1, 1),
                datetime.date(2028, 1, 1),
                datetime.date(2029, 1, 1),
                datetime.date(2030, 1, 1),
            ],
            event=test_event,
        )

    def test_api_rrule_every_three_days(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="DAILY",
            interval=3,
            weekdays_for_weekly=None,
            weekday_for_monthly=None,
            week_for_monthly=None,
            recurrence_end_date=None,
        )
        self.expect_first_items_start(
            recurrence_rule,
            [
                datetime.date(2030, 1, 1),
                datetime.date(2030, 1, 4),
                datetime.date(2030, 1, 7),
                datetime.date(2030, 1, 10),
                datetime.date(2030, 1, 13),
                datetime.date(2030, 1, 16),
                datetime.date(2030, 1, 19),
                datetime.date(2030, 1, 22),
                datetime.date(2030, 1, 25),
                datetime.date(2030, 1, 28),
                datetime.date(2030, 1, 31),
                datetime.date(2030, 2, 3),
                datetime.date(2030, 2, 6),
                datetime.date(2030, 2, 9),
                datetime.date(2030, 2, 12),
            ],
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
        self.expect_first_items_start(
            recurrence_rule,
            [
                datetime.date(2030, 1, 1),
                datetime.date(2030, 1, 7),
                datetime.date(2030, 1, 8),
                datetime.date(2030, 1, 14),
                datetime.date(2030, 1, 15),
                datetime.date(2030, 1, 21),
                datetime.date(2030, 1, 22),
                datetime.date(2030, 1, 28),
                datetime.date(2030, 1, 29),
                datetime.date(2030, 2, 4),
                datetime.date(2030, 2, 5),
                datetime.date(2030, 2, 11),
                datetime.date(2030, 2, 12),
            ],
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
        self.expect_first_items_start(
            recurrence_rule,
            [
                datetime.date(2030, 1, 4),
                datetime.date(2030, 2, 1),
                datetime.date(2030, 3, 1),
                datetime.date(2030, 4, 5),
                datetime.date(2030, 5, 3),
                datetime.date(2030, 6, 7),
                datetime.date(2030, 7, 5),
                datetime.date(2030, 8, 2),
                datetime.date(2030, 9, 6),
                datetime.date(2030, 10, 4),
                datetime.date(2030, 11, 1),
                datetime.date(2030, 12, 6),
            ],
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
        self.expect_first_items_start(
            recurrence_rule,
            [
                datetime.date(2030, 1, 30),
                datetime.date(2030, 2, 27),
                datetime.date(2030, 3, 27),
                datetime.date(2030, 4, 24),
                datetime.date(2030, 5, 29),
                datetime.date(2030, 6, 26),
                datetime.date(2030, 7, 31),
                datetime.date(2030, 8, 28),
                datetime.date(2030, 9, 25),
                datetime.date(2030, 10, 30),
            ],
        )

    def test_api_rrule_second_last_week_in_month(self) -> None:
        recurrence_rule = RecurrenceRule(
            frequency="MONTHLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=weekdays.WEDNESDAY,
            week_for_monthly=weeks.SECOND_LAST,
            recurrence_end_date=None,
        )
        self.expect_first_items_start(
            recurrence_rule,
            [
                datetime.date(2030, 1, 23),
                datetime.date(2030, 2, 20),
                datetime.date(2030, 3, 20),
                datetime.date(2030, 4, 17),
                datetime.date(2030, 5, 22),
                datetime.date(2030, 6, 19),
                datetime.date(2030, 7, 24),
                datetime.date(2030, 8, 21),
                datetime.date(2030, 9, 18),
                datetime.date(2030, 10, 23),
            ],
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
        self.expect_finite_items_start(
            recurrence_rule,
            [
                datetime.date(2030, 1, 6),
                datetime.date(2030, 3, 3),
                datetime.date(2030, 5, 5),
                datetime.date(2030, 7, 7),
                datetime.date(2030, 9, 1),
            ],
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
        self.expect_first_items_start(
            recurrence_rule,
            [
                datetime.date(2030, 1, 1),
                datetime.date(2031, 1, 1),
                datetime.date(2032, 1, 1),
                datetime.date(2033, 1, 1),
                datetime.date(2034, 1, 1),
                datetime.date(2035, 1, 1),
                datetime.date(2036, 1, 1),
                datetime.date(2037, 1, 1),
                datetime.date(2038, 1, 1),
                datetime.date(2039, 1, 1),
                datetime.date(2040, 1, 1),
                datetime.date(2041, 1, 1),
            ],
        )
