import logging

import icalendar
import pytest

from integreat_cms.cms.utils.external_calendar_utils import IcalEventData

logger = logging.getLogger(__name__)

# A list of invalid calendars.
# Format: ( calendar path, error message )
INVALID_CALENDARS = [
    (
        "tests/cms/utils/assets/calendars/invalid_recurrence_rule_wkst_su.ics",
        r"Currently only recurrence rules with weeks starting on Monday are supported \(attempted WKST: SU\)",
    ),
    (
        "tests/cms/utils/assets/calendars/invalid_recurrence_rule_bymonth.ics",
        r"Month of recurrence rule does not match month of event: 2 and 1",
    ),
    (
        "tests/cms/utils/assets/calendars/invalid_recurrence_rule_bymonthday.ics",
        r"Month day of recurrence rule does not match month day of event: 3 and 1",
    ),
    (
        "tests/cms/utils/assets/calendars/invalid_recurrence_rule_conflicting_byday_and_bysetpos.ics",
        r"Conflicting `BYSETPOS` and `BYDAY`: 3 and \['2WE'\]",
    ),
    (
        "tests/cms/utils/assets/calendars/invalid_recurrence_rule_multiple_byday_frequencies.ics",
        r"Cannot support multiple days with frequency right now: \['2WE', '3TH'\]",
    ),
]


@pytest.mark.parametrize("calendar_data", INVALID_CALENDARS)
def test_import_fails(calendar_data: tuple[str, str]) -> None:
    """
    Tests that invalid calendars cannot be imported and that the import fails with the correct error message
    :param calendar_data: A tuple of calendar path and expected error message
    """
    calendar_name, error_msg = calendar_data
    with open(calendar_name, encoding="utf-8") as calendar_file:
        file_contents = calendar_file.read()
    ical = icalendar.Calendar.from_ical(file_contents)

    for event in ical.walk("VEVENT"):
        with pytest.raises(ValueError, match=error_msg):
            data = IcalEventData.from_ical_event(event, "de", 1, logger)
            print(data)
