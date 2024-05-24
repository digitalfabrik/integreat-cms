from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

import icalendar.cal
from cacheops import invalidate_model

from ....cms.constants import status
from ....cms.forms import EventForm, EventTranslationForm
from ....cms.models import Event, EventTranslation, ExternalCalendar
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any


logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to import events from external calendars
    """

    help: str = "Import events from external calendars"

    def handle(self, *args: Any, **options: Any) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param \**options: The supplied keyword options
        """
        self.set_logging_stream()

        calendars = ExternalCalendar.objects.all()
        for calendar in calendars:
            self.import_calendar(calendar)

        invalidate_model(Event)
        invalidate_model(EventTranslation)

    def import_calendar(self, calendar: ExternalCalendar) -> None:
        """
        Imports events from the external calendar

        :param calendar: The calendar to import from
        """
        try:
            ical = calendar.load_ical()
        except IOError as e:
            logger.error("Could not import events from %s: %s", calendar, e)
            return

        calendar_events = set()
        for event in ical.walk("VEVENT"):
            try:
                event_uid = self.import_event(calendar, event)
                if event_uid is not None:
                    calendar_events.add(event_uid)
            except KeyError as e:
                logger.error(
                    "Could not import event because it does not have a required field: %s, missing field: %r",
                    event,
                    e,
                )
                continue

        events_to_delete = Event.objects.filter(external_calendar=calendar).exclude(
            external_event_id__in=calendar_events
        )
        logger.info(
            "Deleting %s unused events: %r", events_to_delete.count(), events_to_delete
        )
        events_to_delete.delete()

    def import_event(
        self, calendar: ExternalCalendar, event: icalendar.cal.Component
    ) -> str | None:
        """
        Imports an event from the external calendar

        :param calendar: The calendar to import from
        :param event: The event that should be imported

        :return: The uid of the event
        """
        language = calendar.region.default_language
        event_id = event.decoded("UID").decode("utf-8")
        title = event.decoded("SUMMARY").decode("utf-8")
        # TODO: When cleaning the form, we convert the content into html, which causes an event translation to always change
        content = (
            event.decoded("DESCRIPTION").decode("utf-8")
            if "DESCRIPTION" in event
            else ""
        )
        start = event.decoded("DTSTART")
        end = event.decoded("DTEND")
        logger.debug(
            "Event(event_id=%s, title=%s, start=%s, end=%s, content=%s)",
            event_id,
            title,
            start,
            end,
            content,
        )

        # Skip this event if it does not have the required tag
        if categories := event.get("categories"):
            if calendar.import_filter_tag and not any(
                category == calendar.import_filter_tag for category in categories.cats
            ):
                logger.info(
                    "Skipping event %s with tags: %s", title, ", ".join(categories.cats)
                )
                return None
        elif calendar.import_filter_tag:
            logger.info("Skipping event %s without tags", title)
            return None

        event_data = {
            "start_date": (
                start.date() if isinstance(start, datetime.datetime) else start
            ),
            "start_time": (
                start.time() if isinstance(start, datetime.datetime) else None
            ),
            "end_date": end.date() if isinstance(end, datetime.datetime) else end,
            "end_time": end.time() if isinstance(end, datetime.datetime) else None,
            "is_all_day": not isinstance(start, datetime.datetime),
            "has_not_location": True,
            "external_calendar": calendar.pk,
            "external_event_id": event_id,
        }

        previously_imported_event_translation = EventTranslation.objects.filter(
            event__external_calendar=calendar,
            event__external_event_id=event_id,
            language=language,
        ).first()
        previously_imported_event = (
            previously_imported_event_translation.event
            if previously_imported_event_translation
            else None
        )

        event_form = EventForm(
            data=event_data,
            instance=previously_imported_event,
            additional_instance_attributes={"region": calendar.region},
        )
        if not event_form.is_valid():
            logger.error("Could not import event: %r", event_form.errors)
            return event_id

        event = event_form.save()

        event_translation_data = {
            "title": title,
            "status": status.PUBLIC,
            "content": content,
        }
        event_translation_form = EventTranslationForm(
            data=event_translation_data,
            instance=previously_imported_event_translation,
            additional_instance_attributes={
                "language": calendar.region.default_language,
                "event": event,
            },
        )
        if not event_translation_form.is_valid():
            logger.error("Could not import event: %r", event_translation_form.errors)
            return event_id

        # TODO: We could look at the sequence number of the ical event too, to see if it has changed.
        # If it hasn't, we don't need to create forms and can quickly skip it
        if event_form.has_changed() or event_translation_form.has_changed():
            event_translation = event_translation_form.save()
            logger.success("Imported event %r, %r", event, event_translation)  # type: ignore[attr-defined]
        else:
            logger.info("Event %r has not changed", event_translation_form.instance)

        return event_id
