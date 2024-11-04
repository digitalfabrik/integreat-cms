"""
Utility functions for working with external calendars
"""

from __future__ import annotations

import dataclasses
import datetime
import logging

import icalendar.cal
from django.utils.translation import gettext as _
from icalendar.prop import vCategory

from integreat_cms.cms.constants import status
from integreat_cms.cms.forms import EventForm, EventTranslationForm
from integreat_cms.cms.models import EventTranslation, ExternalCalendar
from integreat_cms.cms.utils.content_utils import clean_content


# pylint: disable=too-many-instance-attributes
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
    categories: list[str]
    external_calendar_id: int

    @classmethod
    def from_ical_event(
        cls,
        event: icalendar.cal.Component,
        language_slug: str,
        external_calendar_id: int,
        logger: logging.Logger,
    ) -> IcalEventData:
        """
        Reads an ical event and constructs an instance of this class from it
        :param event: The ical event
        :param language_slug: The slug of the language of this event
        :param external_calendar_id: The id of the external calendar of this event
        :param logger: The logger to use
        :return: An instance of IcalEventData
        """
        # pylint: disable=too-many-locals
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


def import_events(calendar: ExternalCalendar, logger: logging.Logger) -> None:
    """
    Imports events from this calendar and sets or clears the errors field of the calendar

    :param calendar: The external calendar
    :param logger: The logger to use
    """

    errors: list[str] = []

    _import_events(calendar, errors, logger)

    if errors:
        calendar.errors = "\n".join(errors)
    else:
        calendar.errors = ""

    calendar.save()


def _import_events(
    calendar: ExternalCalendar, errors: list[str], logger: logging.Logger
) -> None:
    """
    Imports events from this calendar and sets or clears the errors field of the calendar

    :param calendar: The external calendar
    :param logger: The logger to use
    """
    try:
        ical = calendar.load_ical()
    except IOError as e:
        logger.error("Could not import events from %s: %s", calendar, e)
        errors.append(_("Could not access the url of this external calendar"))
        return
    except ValueError as e:
        logger.error("Malformed calendar %s: %s", calendar, e)
        errors.append(
            _("The data provided by the url of this external calendar is invalid")
        )
        return

    calendar_events = set()
    for event in ical.walk("VEVENT"):
        try:
            if (event_uid := import_event(calendar, event, errors, logger)) is not None:
                calendar_events.add(event_uid)
        except KeyError as e:
            logger.error(
                "Could not import event because it does not have a required field: %s, missing field: %r",
                event,
                e,
            )
            errors.append(
                _(
                    "Could not import event because it is missing a required field: {}"
                ).format(e)
            )
            continue

    events_to_delete = calendar.events.exclude(external_event_id__in=calendar_events)
    logger.info(
        "Deleting %s unused events: %r", events_to_delete.count(), events_to_delete
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

    event_data = IcalEventData.from_ical_event(
        event, language.slug, calendar.pk, logger
    )

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

    event_form = EventForm(
        data=event_data.to_event_form_data(),
        instance=previously_imported_event,
        additional_instance_attributes={"region": calendar.region},
    )
    if not event_form.is_valid():
        logger.error("Could not import event: %r", event_form.errors)
        errors.append(
            _("Could not import '{}': {}").format(event_data.title, event_form.errors)
        )
        return event_data.event_id

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
                event_data.title, event_translation_form.errors
            )
        )
        return event_data.event_id

    # We could look at the sequence number of the ical event too, to see if it has changed.
    # If it hasn't, we don't need to create forms and can quickly skip it
    if event_form.has_changed() or event_translation_form.has_changed():
        event_translation = event_translation_form.save()
        logger.success("Imported event %r, %r", event, event_translation)  # type: ignore[attr-defined]
    else:
        logger.info("Event %r has not changed", event_translation_form.instance)

    return event_data.event_id
