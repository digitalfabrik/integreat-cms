"""
Form for submitting filter requests
"""
import logging

from django import forms

from ...constants import all_day, recurrence, events_time_range

logger = logging.getLogger(__name__)


class EventFilterForm(forms.Form):
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

    def filters_visible(self):
        """
        This function determines whether the filter form is visible by default.

        :return: whether any filters (other than search) were changed
        :rtype: bool
        """
        return self.has_changed() and self.changed_data != ["query"]
