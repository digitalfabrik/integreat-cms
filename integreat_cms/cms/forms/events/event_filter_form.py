"""
Form for submitting filter requests
"""

from __future__ import annotations

import logging
import zoneinfo
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from django import forms
from django.db.models import F, Q

if TYPE_CHECKING:
    from ...models import POI, Region
    from ...models.events.event import EventQuerySet

from ...constants import all_day, calendar_filters, events_time_range, recurrence
from ...models import EventTranslation
from ..custom_filter_form import CustomFilterForm

logger = logging.getLogger(__name__)


class EventFilterForm(CustomFilterForm):
    """
    Form to filter the event list
    """

    all_day = forms.TypedMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "default-checked"}),
        choices=all_day.CHOICES,
        initial=[key for (key, val) in all_day.CHOICES],
        coerce=all_day.DATATYPE,
        required=False,
    )

    recurring = forms.TypedMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "default-checked"}),
        choices=recurrence.CHOICES,
        initial=[key for (key, val) in recurrence.CHOICES],
        coerce=recurrence.DATATYPE,
        required=False,
    )

    date_from = forms.DateField(
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "default-value", "data-default-value": ""},
        ),
        required=False,
    )
    date_to = forms.DateField(
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "default-value", "data-default-value": ""},
        ),
        required=False,
    )

    events_time_range = forms.MultipleChoiceField(
        widget=forms.widgets.CheckboxSelectMultiple(
            attrs={
                "data-default-checked-value": events_time_range.UPCOMING,
                "data-custom-time-range-value": events_time_range.CUSTOM,
            },
        ),
        choices=events_time_range.CHOICES,
        initial=[events_time_range.UPCOMING],
        required=False,
    )

    imported_event = forms.TypedMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "default-checked"}),
        choices=calendar_filters.CHOICES,
        initial=[key for (key, val) in calendar_filters.CHOICES],
        coerce=calendar_filters.DATATYPE,
        required=False,
    )

    poi_id = forms.IntegerField(widget=forms.HiddenInput, initial=-1, required=False)

    query = forms.CharField(required=False)

    def filter_events_by_time_range(self, events: EventQuerySet) -> EventQuerySet:
        """
        Filter events by time range

        :param events: the unfiltered events
        :param events: the filtered events
        """
        if not self.is_enabled:
            return events

        cleaned_time_range = self.cleaned_data["events_time_range"]
        if not cleaned_time_range or set(cleaned_time_range) == set(
            events_time_range.ALL_EVENTS,
        ):
            return events

        if events_time_range.CUSTOM in cleaned_time_range:
            tzinfo = zoneinfo.ZoneInfo(self.region.timezone)
            if date_from := self.cleaned_data["date_from"]:
                from_local = datetime.combine(date_from, time.min, tzinfo=tzinfo)
            else:
                from_local = datetime.min.replace(tzinfo=zoneinfo.ZoneInfo(key="UTC"))
            to_local = datetime.combine(
                self.cleaned_data["date_to"] or date.max,
                time.max,
                tzinfo=tzinfo,
            )
            events = events.filter_upcoming(from_local).filter(end__lte=to_local)
        elif events_time_range.UPCOMING in cleaned_time_range:
            events = events.filter_upcoming()
        elif events_time_range.PAST in cleaned_time_range:
            events = events.filter_completed()
        return events

    def filter_events_by_location(
        self, events: EventQuerySet
    ) -> tuple[EventQuerySet, POI]:
        """
        Filter events by location

        :param events: the unfiltered events
        :param events: the filtered events
        """
        if poi := self.region.pois.filter(id=self.cleaned_data["poi_id"]).first():
            events = events.filter(location=poi)
        return events, poi

    def filter_events_by_all_day(self, events: EventQuerySet) -> EventQuerySet:
        """
        Filter events by all-day property

        :param events: the unfiltered events
        :param events: the filtered events
        """
        if (
            len(self.cleaned_data["all_day"]) == len(all_day.CHOICES)
            or not self.cleaned_data["all_day"]
        ):
            return events
        if all_day.ALL_DAY in self.cleaned_data["all_day"]:
            events = events.filter(
                start__time=time.min,
                end__time=time.max.replace(second=0, microsecond=0),
            )
        elif all_day.NOT_ALL_DAY in self.cleaned_data["all_day"]:
            events = events.exclude(
                start__time=time.min,
                end__time=time.max.replace(second=0, microsecond=0),
            )
        return events

    def filter_events_by_recurrence(self, events: EventQuerySet) -> EventQuerySet:
        """
        Filter events by recurrence

        :param events: the unfiltered events
        :param events: the filtered events
        """
        if (
            len(self.cleaned_data["recurring"]) == len(recurrence.CHOICES)
            or not self.cleaned_data["recurring"]
        ):
            return events

        query = Q()

        if recurrence.RECURRING in self.cleaned_data["recurring"]:
            query |= Q(recurrence_rule__isnull=False)
        if recurrence.ONE_TIME in self.cleaned_data["recurring"]:
            query |= Q(start__date=F("end__date"), recurrence_rule__isnull=True)
        if recurrence.LONG_TERM in self.cleaned_data["recurring"]:
            query |= Q(~Q(start__date=F("end__date")), recurrence_rule__isnull=True)

        return events.filter(query)

    def filter_events_by_imported_event(self, events: EventQuerySet) -> EventQuerySet:
        """
        Filter events by imported event

        :param events: the unfiltered events
        :param events: the filtered events
        """
        if (
            len(self.cleaned_data["imported_event"]) == len(calendar_filters.CHOICES)
            or not self.cleaned_data["imported_event"]
        ):
            return events
        if (
            calendar_filters.EVENT_NOT_FROM_EXTERNAL_CALENDAR
            in self.cleaned_data["imported_event"]
        ):
            events = events.filter(external_calendar__isnull=True)
        elif (
            calendar_filters.EVENT_FROM_EXTERNAL_CALENDAR
            in self.cleaned_data["imported_event"]
        ):
            events = events.filter(external_calendar__isnull=False)
        return events

    def search_events(self, events: EventQuerySet) -> tuple[EventQuerySet, str]:
        """
        Search events for given query

        :param events: The unsearched events
        :return events: The searched events
        """
        if query := self.cleaned_data["query"]:
            event_ids = EventTranslation.search(
                self.region, self.language_slug, query
            ).values(
                "event__pk",
            )
            events = events.filter(pk__in=event_ids)
        return events, query

    def apply(
        self,
        events: EventQuerySet,
        region: Region,
        language_slug: str,
    ) -> tuple[EventQuerySet, POI, str]:
        """
        Filter the events according to the given filter data

        :param events: The list of events
        :param region: The current region
        :param language_slug: The slug of the current language
        :return: The filtered list of events, the poi used for filtering, and the search query
        """
        self.region = region
        self.language_slug = language_slug

        if not self.is_enabled:
            events = events.filter_upcoming()

        events = self.filter_events_by_time_range(events)
        events, poi = self.filter_events_by_location(events)
        events = self.filter_events_by_all_day(events)
        events = self.filter_events_by_recurrence(events)
        events = self.filter_events_by_imported_event(events)
        events, query = self.search_events(events)

        return events, poi, query
