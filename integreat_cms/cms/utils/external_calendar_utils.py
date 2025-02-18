"""
Utility functions for working with external calendars
"""

from __future__ import annotations

import dataclasses
import datetime
from typing import Any, Self, TYPE_CHECKING

from django.utils.translation import gettext as _
from icalendar.prop import vCategory, vDDDTypes, vFrequency, vInt, vRecur, vWeekday

from integreat_cms.cms.constants import frequency, status
from integreat_cms.cms.constants.weekdays import RRULE_WEEKDAY_TO_WEEKDAY
from integreat_cms.cms.constants.weeks import RRULE_WEEK_TO_WEEK
from integreat_cms.cms.forms import EventForm, EventTranslationForm, RecurrenceRuleForm
from integreat_cms.cms.models import EventTranslation, ExternalCalendar, RecurrenceRule
from integreat_cms.cms.utils.content_utils import clean_content

if TYPE_CHECKING:
    import logging

    import icalendar


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImportResult:
    """
    Datatype for the result of `import_event`
    """

    number_of_errors: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class IcalEventData:
    """
    Holds data extracted from ical events
    """

    event_id: str
    title: str
    content: str
    start_date: datetime.date
    start_time: datetime.time | None
    end_date: datetime.date
    end_time: datetime.time | None
    is_all_day: bool
    recurrence_rule: RecurrenceRuleData | None
    categories: list[str]
    external_calendar_id: int

    @classmethod
    def from_ical_event(
        cls,
        event: icalendar.cal.Component,
        language_slug: str,
        external_calendar_id: int,
        logger: logging.Logger,
    ) -> Self:
        """
        Reads an ical event and constructs an instance of this class from it
        :param event: The ical event
        :param language_slug: The slug of the language of this event
        :param external_calendar_id: The id of the external calendar of this event
        :param logger: The logger to use
        :return: An instance of IcalEventData
        :raises ValueError: If the data are invalid
        """
        event_id = event.decoded("UID").decode("utf-8")
        title = event.decoded("SUMMARY").decode("utf-8")
        content = clean_content(
            content=(
                event.decoded("DESCRIPTION").decode("utf-8")
                if "DESCRIPTION" in event
                else ""
            ).replace("\n", "<br>"),
            language_slug=language_slug,
        )
        start = event.decoded("DTSTART")
        end = event.decoded("DTEND")

        # Categories can be a "vCategory" object, a list of such objects, or be missing
        categories = event.get("categories", [])
        categories = (
            categories.cats
            if isinstance(categories, vCategory)
            else [
                category
                for sub_categories in categories
                for category in sub_categories.cats
            ]
        )

        logger.debug(
            "Event(event_id=%s, title=%s, start=%s, end=%s, content=%s...)",
            event_id,
            title,
            start,
            end,
            content[:32],
        )

        is_all_day = not (
            isinstance(start, datetime.datetime) and isinstance(end, datetime.datetime)
        )
        if is_all_day:
            start_date, start_time = start, None
            end_date, end_time = end - datetime.timedelta(days=1), None
        else:
            start_date, start_time = start.date(), start.time()
            end_date, end_time = end.date(), end.time()

        recurrence_rule = None
        if "RRULE" in event:
            if event.decoded("RRULE")["FREQ"] == ["DAILY"]:
                raise ValueError("Daily events are not allowed anymore.")
            end_date = start_date
            recurrence_rule = RecurrenceRuleData.from_ical_rrule(
                recurrence_rule=event.decoded("RRULE"),
                start=start_date,
                logger=logger,
            )

        return cls(
            event_id=event_id,
            title=title,
            content=content,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            is_all_day=is_all_day,
            external_calendar_id=external_calendar_id,
            categories=categories,
            recurrence_rule=recurrence_rule,
        )

    def to_event_form_data(self) -> dict:
        """
        Returns a dictionary of relevant data for the event form
        :return: Dict of relevant data
        """
        return {
            "start_date": self.start_date,
            "start_time": self.start_time,
            "end_date": self.end_date,
            "end_time": self.end_time,
            "is_all_day": self.is_all_day,
            "is_recurring": bool(self.recurrence_rule),
            "has_not_location": True,
            "external_calendar": self.external_calendar_id,
            "external_event_id": self.event_id,
        }

    def to_event_translation_form_data(self) -> dict:
        """
        Returns a dictionary of relevant data for the event translation form
        :return: Dict of relevant data
        """
        return {"title": self.title, "status": status.PUBLIC, "content": self.content}

    def to_recurrence_rule_form_data(self) -> dict:
        """
        Returns a dictionary of relevant data for the recurrence rule form
        :return: Dict of relevant data
        :raises ValueError: If the recurrence rule cannot be mapped to form data
        """
        if not self.recurrence_rule:
            return {}

        return self.recurrence_rule.to_form_data()


@dataclasses.dataclass(frozen=True, kw_only=True)
class RecurrenceRuleData:
    """
    This dataclass contains all relevant data for producing arguments for a recurrence rule from an ical rrule.
    """

    frequency: vFrequency
    interval: vInt
    until: vDDDTypes | None
    by_day: list[vWeekday] | None
    by_set_pos: int | None

    @classmethod
    def from_ical_rrule(
        cls,
        recurrence_rule: vRecur,
        start: datetime.date,
        logger: logging.Logger,
    ) -> Self:
        """
        Constructs this class from an ical recurrence rule.
        :return: An instance of this class
        :raises ValueError: If the recurrence rule cannot be mapped to this class
        """

        def pop_single_value(name: str, *, required: bool = False) -> Any:
            """
            Removes the key from the recurrence rule and returns a single value or ``None``, if ``required`` is True
            :return: A single value from the recurrence rule or ``None``
            :raises ValueError: If the recurrence rule contains multiple value for the given name
            """
            match recurrence_rule.pop(name):
                case [] | None if not required:
                    return None
                case [single]:
                    return single
                case other:
                    raise ValueError(f"Expected a single value for {name}, got {other}")

        logger.debug("Recurrence rule: %s", recurrence_rule)
        frequency_ = pop_single_value("FREQ", required=True)
        interval = pop_single_value("INTERVAL") or 1
        until = pop_single_value("UNTIL")
        by_day = recurrence_rule.pop("BYDAY")
        by_set_pos = pop_single_value("BYSETPOS")

        # by_set_pos can also be specified in `by_day`. We don't support multiple days with `by_set_pos` right now, though.
        if by_day and len(by_day) == 1:
            if by_set_pos is not None and by_day[0].relative is not None:
                raise ValueError(
                    f"Conflicting `BYSETPOS` and `BYDAY`: {by_set_pos} and {by_day}",
                )
            by_set_pos = by_day[0].relative or by_set_pos
            by_day[0] = by_day[0].weekday
        elif by_day:
            updated_days = []
            for day in by_day:
                updated_days.append(day.weekday)
                if day.relative is not None:
                    raise ValueError(
                        f"Cannot support multiple days with frequency right now: {by_day}",
                    )
            by_day = updated_days

        # WKST currently always has to be monday (or unset, because it defaults do monday)
        if (wkst := pop_single_value("WKST")) and wkst.lower() != "mo":
            raise ValueError(
                f"Currently only recurrence rules with weeks starting on Monday are supported (attempted WKST: {wkst})",
            )

        if (
            by_month_day := pop_single_value("BYMONTHDAY")
        ) and by_month_day != start.day:
            raise ValueError(
                f"Month day of recurrence rule does not match month day of event: {by_month_day} and {start.day}",
            )

        if (by_month := pop_single_value("BYMONTH")) and by_month != start.month:
            raise ValueError(
                f"Month of recurrence rule does not match month of event: {by_month} and {start.month}",
            )

        if len(recurrence_rule) > 0:
            raise ValueError(
                f"Recurrence rule contained unsupported attribute(s): {list(recurrence_rule.keys())}",
            )

        return cls(
            frequency=frequency_,
            interval=interval,
            until=until,
            by_day=by_day,
            by_set_pos=by_set_pos,
        )

    def to_form_data(self) -> dict:
        """
        Creates a dictionary that can be passed as form data to the recurrence rule form
        :return: Dict of relevant data
        :raises ValueError: If the recurrence rule cannot be mapped to form data
        """
        weekdays_for_weekly = None
        weekday_for_monthly = None
        week_for_monthly = None
        match self.frequency:
            case frequency.DAILY:
                raise ValueError('Frequency "Daily" is not supported anymore')
            case frequency.WEEKLY:
                weekdays_for_weekly = self.decode_by_day()
            case frequency.MONTHLY:
                week_for_monthly = self.decode_by_set_pos()

                weekdays = self.decode_by_day()
                if len(weekdays) != 1:
                    raise ValueError(f"Unsupported weekday for monthly: {self.by_day}")
                weekday_for_monthly = weekdays[0]
            case frequency.YEARLY:
                pass
            case other:
                raise ValueError(f"Unsupported frequency: {other}")

        return {
            "frequency": self.frequency,
            "interval": self.interval,
            "recurrence_end_date": self.until,
            "has_recurrence_end_date": bool(self.until),
            "weekdays_for_weekly": weekdays_for_weekly,
            "weekday_for_monthly": weekday_for_monthly,
            "week_for_monthly": week_for_monthly,
        }

    def decode_by_set_pos(self) -> int:
        """
        :return: The correct ``cms.constants.weeks`` value for the set pos
        :raises ValueError: If the by_set_pos value is not supported
        """
        if self.by_set_pos is None:
            raise ValueError("by_set_pos must not be None")
        if not (decoded := RRULE_WEEK_TO_WEEK.get(self.by_set_pos)):
            raise ValueError(f"Unknown value for by_set_pos: {self.by_set_pos}")
        return decoded

    def decode_by_day(self) -> list[int]:
        """
        :return: The correct ``cms.constants.weeks`` value for the day of the week
        :raises ValueError: If the by_day value is not supported
        """
        if not self.by_day:
            raise ValueError("Missing required value for by_day")
        weekdays_or_none = [
            RRULE_WEEKDAY_TO_WEEKDAY.get(weekday) for weekday in self.by_day
        ]
        weekdays = [weekday for weekday in weekdays_or_none if weekday is not None]
        if len(weekdays) != len(weekdays_or_none):
            raise ValueError(f"Unknown value for weekday: {self.by_day}")
        return weekdays


def import_events(calendar: ExternalCalendar, logger: logging.Logger) -> ImportResult:
    """
    Imports events from this calendar and sets or clears the errors field of the calendar

    :param calendar: The external calendar
    :param logger: The logger to use
    :return: the result of the import (count of errors and successes).
    """

    errors: list[str] = []

    _import_events(calendar, errors, logger)

    if errors:
        calendar.errors = "\n".join(errors)
    else:
        calendar.errors = ""

    calendar.save()
    return ImportResult(number_of_errors=len(errors))


def _import_events(
    calendar: ExternalCalendar,
    errors: list[str],
    logger: logging.Logger,
) -> None:
    """
    Imports events from this calendar and sets or clears the errors field of the calendar

    :param calendar: The external calendar
    :param logger: The logger to use
    """
    try:
        ical = calendar.load_ical()
    except OSError:
        logger.exception("Could not import events from %s", calendar)
        errors.append(_("Could not access the url of this external calendar"))
        return
    except ValueError:
        logger.exception("Malformed calendar %s", calendar)
        errors.append(
            _("The data provided by the url of this external calendar is invalid"),
        )
        return

    calendar_events = set()
    for event in ical.walk("VEVENT"):
        try:
            if (event_uid := import_event(calendar, event, errors, logger)) is not None:
                calendar_events.add(event_uid)
        except KeyError as e:
            logger.exception(
                "Could not import event because it does not have a required field: %s, missing field",
                event,
            )
            errors.append(
                _(
                    "Could not import event because it is missing a required field: {}",
                ).format(e),
            )
            continue

    events_to_delete = calendar.events.exclude(external_event_id__in=calendar_events)
    logger.info(
        "Deleting %s unused events: %r",
        events_to_delete.count(),
        events_to_delete,
    )
    events_to_delete.delete()


def import_event(
    calendar: ExternalCalendar,
    event: icalendar.cal.Component,
    errors: list[str],
    logger: logging.Logger,
) -> str | None:
    """
    Imports an event from the external calendar

    :param calendar: The external calendar
    :param event: The event that should be imported
    :param errors: A list to which errors will be logged
    :param logger: The logger to use

    :return: The uid of the event
    """
    language = calendar.region.default_language

    try:
        event_data = IcalEventData.from_ical_event(
            event,
            language.slug,
            calendar.pk,
            logger,
        )
    except ValueError as e:
        logger.exception("Could not import event: %r due to error", event)
        errors.append(_("Could not import '{}': {}").format(event.get("SUMMARY"), e))
        try:
            return event.decoded("UID").decode("utf-8")
        except (KeyError, UnicodeError):
            return None

    # Skip this event if it does not have the required tag
    if calendar.import_filter_category and not any(
        category == calendar.import_filter_category
        for category in event_data.categories
    ):
        logger.info(
            "Skipping event %s with tags: [%s]",
            event_data.title,
            ", ".join(event_data.categories),
        )
        return None

    previously_imported_event_translation = EventTranslation.objects.filter(
        event__external_calendar=calendar,
        event__external_event_id=event_data.event_id,
        language=language,
    ).first()
    previously_imported_event = (
        previously_imported_event_translation.event
        if previously_imported_event_translation
        else None
    )
    previously_imported_recurrence_rule = RecurrenceRule.objects.filter(
        event__external_calendar=calendar,
        event__external_event_id=event_data.event_id,
    ).first()

    event_form = EventForm(
        data=event_data.to_event_form_data(),
        instance=previously_imported_event,
        additional_instance_attributes={"region": calendar.region},
    )
    if not event_form.is_valid():
        logger.error("Could not import event: %r", event_form.errors)
        errors.append(
            _("Could not import '{}': {}").format(event_data.title, event_form.errors),
        )
        return event_data.event_id

    try:
        recurrence_rule_form_data = event_data.to_recurrence_rule_form_data()
    except ValueError as e:
        logger.exception(
            "Could not import event due to unsupported recurrence rule:\n%s",
            event_data,
        )
        errors.append(
            _("Could not import '{}': Unsupported recurrence rule").format(
                event_data.title,
                e,
            ),
        )
        return event_data.event_id
    recurrence_rule_form = RecurrenceRuleForm(
        data=recurrence_rule_form_data,
        instance=previously_imported_recurrence_rule,
        event_start_date=event_form.cleaned_data.get("start_date"),
    )
    if recurrence_rule_form_data and not recurrence_rule_form.is_valid():
        logger.error(
            "Could not import recurrence rule: %r",
            recurrence_rule_form.errors,
        )
        errors.append(
            _("Could not import '{}': {}").format(
                event_data.title,
                recurrence_rule_form.errors,
            ),
        )
        return event_data.event_id

    if recurrence_rule_form_data:
        event_form.instance.recurrence_rule = recurrence_rule_form.save()
    elif event_form.instance.recurrence_rule:
        event_form.instance.recurrence_rule.delete()
        event_form.instance.recurrence_rule = None

    event = event_form.save()

    event_translation_form = EventTranslationForm(
        data=event_data.to_event_translation_form_data(),
        instance=previously_imported_event_translation,
        additional_instance_attributes={
            "language": language,
            "event": event,
        },
    )
    if not event_translation_form.is_valid():
        logger.error("Could not import event: %r", event_translation_form.errors)
        errors.append(
            _("Could not import '{}': {}").format(
                event_data.title,
                event_translation_form.errors,
            ),
        )
        return event_data.event_id

    # We could look at the sequence number of the ical event too, to see if it has changed.
    # If it hasn't, we don't need to create forms and can quickly skip it
    if (
        event_form.has_changed()
        or event_translation_form.has_changed()
        or recurrence_rule_form.has_changed()
    ):
        event_translation = event_translation_form.save()
        logger.info(
            "Imported event %r, %r, %r",
            event,
            event_translation,
            event.recurrence_rule,
        )  # type: ignore[attr-defined]
    else:
        logger.info("Event %r has not changed", event_translation_form.instance)

    return event_data.event_id
