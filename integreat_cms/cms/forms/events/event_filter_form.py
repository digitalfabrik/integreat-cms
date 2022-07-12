"""
Form for submitting filter requests
"""
from datetime import date, time
import logging

from django import forms

from ..custom_filter_form import CustomFilterForm
from ...constants import all_day, recurrence, events_time_range
from ...models import EventTranslation

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
            }
        ),
        choices=events_time_range.CHOICES,
        initial=[events_time_range.UPCOMING],
        required=False,
    )
    poi_id = forms.IntegerField(widget=forms.HiddenInput, initial=-1, required=False)

    query = forms.CharField(required=False)

    # pylint: disable=too-many-branches
    def apply(self, events, region, language_slug):
        """
        Filter the events according to the given filter data

        :param events: The list of events
        :type events: list

        :param region: The current region
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param language_slug: The slug of the current language
        :type language_slug: str

        :return: The filtered list of events, the poi used for filtering, and the search query
        :rtype: tuple
        """
        if not self.is_enabled:
            events = events.filter_upcoming()
            return events, None, None

        # Filter events by time range
        cleaned_time_range = self.cleaned_data["events_time_range"]
        if len(cleaned_time_range) == 0 or set(cleaned_time_range) == set(
            events_time_range.ALL_EVENTS
        ):
            # Either post & upcoming or no checkboxes are checked => skip filtering
            pass
        elif events_time_range.CUSTOM in cleaned_time_range:
            # Filter events for their start and end
            events = events.filter_upcoming(
                self.cleaned_data["date_from"] or date.min
            ).filter(end_date__lte=self.cleaned_data["date_to"] or date.max)
        elif events_time_range.UPCOMING in cleaned_time_range:
            # Only upcoming events
            events = events.filter_upcoming()
        elif events_time_range.PAST in cleaned_time_range:
            # Only past events
            events = events.filter_completed()
        # Filter events for their location
        poi = region.pois.filter(id=self.cleaned_data["poi_id"]).first()
        if poi is not None:
            events = events.filter(location=poi)
        # Filter events for their all-day property
        if (
            len(self.cleaned_data["all_day"]) == len(all_day.CHOICES)
            or len(self.cleaned_data["all_day"]) == 0
        ):
            # Either all or no checkboxes are checked => skip filtering
            pass
        elif all_day.ALL_DAY in self.cleaned_data["all_day"]:
            # Filter for all-day events
            events = events.filter(
                start_time=time.min,
                end_time=time.max.replace(second=0, microsecond=0),
            )
        elif all_day.NOT_ALL_DAY in self.cleaned_data["all_day"]:
            # Exclude all-day events
            events = events.exclude(
                start_time=time.min,
                end_time=time.max.replace(second=0, microsecond=0),
            )
        # Filter events for recurrence
        if (
            len(self.cleaned_data["recurring"]) == len(recurrence.CHOICES)
            or len(self.cleaned_data["recurring"]) == 0
        ):
            # Either all or no checkboxes are checked => skip filtering
            pass
        elif recurrence.RECURRING in self.cleaned_data["recurring"]:
            # Only recurring events
            events = events.filter(recurrence_rule__isnull=False)
        elif recurrence.NOT_RECURRING in self.cleaned_data["recurring"]:
            # Only non-recurring events
            events = events.filter(recurrence_rule__isnull=True)
        # Filter events by the search query
        query = self.cleaned_data["query"]
        if query:
            event_ids = EventTranslation.search(region, language_slug, query).values(
                "event__pk"
            )
            events = events.filter(pk__in=event_ids)

        return events, poi, query
