"""
Test tree mutex for page tree
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

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


