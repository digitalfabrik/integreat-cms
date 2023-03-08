"""
Test module for RecurrenceRule class
"""
import datetime

import pytz

from integreat_cms.cms.models import Event, RecurrenceRule

# pylint: disable=missing-function-docstring
class TestCreatingIcalRule:
    """
    Test whether to_ical_rrule_string function is calculating the rrule correctly
    """

    test_event = Event(
        start=datetime.datetime(2030, 1, 1, 11, 30, 0, 0, pytz.UTC),
        end=datetime.datetime(2030, 1, 1, 12, 30, 0, 0, pytz.UTC),
    )

    def test_api_rrule_every_year_start_date_in_the_past(self):
        recurrence_rule = RecurrenceRule(
            frequency="YEARLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=None,
            week_for_monthly=None,
            recurrence_end_date=None,
        )
        test_event = Event(
            start=datetime.datetime(2020, 1, 1, 11, 30, 0, 0, pytz.UTC),
            end=datetime.datetime(2030, 1, 1, 12, 30, 0, 0, pytz.UTC),
        )
        test_event.recurrence_rule = recurrence_rule
        ical_rrule = recurrence_rule.to_ical_rrule_string()
        assert ical_rrule == "DTSTART:20200101T113000\nRRULE:FREQ=YEARLY"

    def check_rrule(self, recurrence_rule, expected):
        self.test_event.recurrence_rule = recurrence_rule
        ical_rrule = recurrence_rule.to_ical_rrule_string()
        assert ical_rrule == expected

    def test_api_rrule_every_three_days(self):
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

    def test_api_rrule_weekly(self):
        recurrence_rule = RecurrenceRule(
            frequency="WEEKLY",
            interval=1,
            weekdays_for_weekly=[0, 1],
            weekday_for_monthly=None,
            week_for_monthly=None,
            recurrence_end_date=None,
        )
        self.check_rrule(
            recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU"
        )

    def test_api_rrule_monthly(self):
        recurrence_rule = RecurrenceRule(
            frequency="MONTHLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=4,
            week_for_monthly=1,
            recurrence_end_date=None,
        )
        self.check_rrule(
            recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=MONTHLY;BYDAY=+1FR"
        )

    def test_api_rrule_bimonthly_until(self):
        recurrence_rule = RecurrenceRule(
            frequency="MONTHLY",
            interval=2,
            weekdays_for_weekly=None,
            weekday_for_monthly=6,
            week_for_monthly=1,
            recurrence_end_date=datetime.date(2030, 10, 19),
        )
        self.check_rrule(
            recurrence_rule,
            "DTSTART:20300101T113000\nRRULE:FREQ=MONTHLY;INTERVAL=2;UNTIL=20301019T235959;BYDAY=+1SU",
        )

    def test_api_rrule_yearly(self):
        recurrence_rule = RecurrenceRule(
            frequency="YEARLY",
            interval=1,
            weekdays_for_weekly=None,
            weekday_for_monthly=None,
            week_for_monthly=None,
            recurrence_end_date=None,
        )
        self.check_rrule(recurrence_rule, "DTSTART:20300101T113000\nRRULE:FREQ=YEARLY")
