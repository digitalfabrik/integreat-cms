import logging
import zoneinfo
from datetime import time, timedelta, datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from ...models import Event
from ..custom_model_form import CustomModelForm
from ..icon_widget import IconWidget

logger = logging.getLogger(__name__)


class EventForm(CustomModelForm):
    """
    Form for creating and modifying event objects
    """

    # Whether or not the event is all day
    is_all_day = forms.BooleanField(required=False, label=_("All-day"))
    # Whether or not the event is recurring
    is_recurring = forms.BooleanField(
        required=False,
        label=_("Recurring"),
        help_text=_("Determines whether the event is repeated at regular intervals."),
    )
    # Whether or not the event has a physical location
    has_not_location = forms.BooleanField(
        required=False,
        label=_("Event does not have a physical location"),
        label_suffix="",
        help_text=_("Determines whether the event is assigned to a physical location."),
    )
    # Specific fields for the date and time of the start and end of the event
    # These Fields will be used for form the start and date fields of the event model
    start_date = forms.DateField(
        label=_("start date"),
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label=_("end date"),
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    start_time = forms.TimeField(
        label=_("start time"),
        required=False,
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    )
    end_time = forms.TimeField(
        label=_("end time"),
        required=False,
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Event
        #: The fields of the model which should be handled by this form
        fields = [
            "start",
            "end",
            "icon",
            "location",
        ]
        #: The widgets which are used in this form
        widgets = {
            "icon": IconWidget(),
        }
        error_messages = {
            "location": {
                "invalid_choice": _(
                    "Either disable the event location or provide a valid location"
                ),
            },
        }

    def __init__(self, **kwargs):
        r"""
        Initialize event form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """

        # Instantiate CustomModelForm
        super().__init__(**kwargs)
        # Set the required tag for start and end field to false,
        # since they will be set later in the clean method
        self.fields["start"].required = False
        self.fields["end"].required = False
        if self.instance.id:
            # Initialize non-model fields based on event
            self.fields["start_date"].initial = self.instance.start_local.date()
            self.fields["start_time"].initial = self.instance.start_local.time()
            self.fields["end_date"].initial = self.instance.end_local.date()
            self.fields["end_time"].initial = self.instance.end_local.time()
            self.fields["is_all_day"].initial = self.instance.is_all_day
            self.fields["is_recurring"].initial = self.instance.is_recurring
            self.fields["has_not_location"].initial = not self.instance.has_location

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        # make self.data mutable to allow values to be changed manually
        self.data = self.data.copy()

        if cleaned_data.get("is_all_day"):
            cleaned_data["start_time"] = time.min
            self.data["start_time"] = time.min
            # Strip seconds and microseconds because our time fields only has hours and minutes
            cleaned_data["end_time"] = time.max.replace(second=0, microsecond=0)
            self.data["end_time"] = time.max.replace(second=0, microsecond=0)
        else:
            # If at least one of the time fields are missing, show an error
            if not cleaned_data.get("start_time"):
                self.add_error(
                    "start_time",
                    forms.ValidationError(
                        _("If the event is not all-day, the start time is required"),
                        code="required",
                    ),
                )
            if not cleaned_data.get("end_time"):
                self.add_error(
                    "end_time",
                    forms.ValidationError(
                        _("If the event is not all-day, the end time is required"),
                        code="required",
                    ),
                )
            elif cleaned_data["start_time"] == time.min and cleaned_data[
                "end_time"
            ] == time.max.replace(second=0, microsecond=0):
                self.data["is_all_day"] = True

        if cleaned_data.get("end_date") and cleaned_data.get("start_date"):
            if cleaned_data.get("end_date") < cleaned_data.get("start_date"):
                # If both dates are given, check if they are valid
                self.add_error(
                    "end_date",
                    forms.ValidationError(
                        _(
                            "The end of the event can't be before the start of the event"
                        ),
                        code="invalid",
                    ),
                )
            elif cleaned_data.get("end_date") == cleaned_data.get("start_date"):
                # If both dates are identical, check the times
                if cleaned_data.get("end_time") and cleaned_data.get("start_time"):
                    # If both times are given, check if they are valid
                    if cleaned_data.get("end_time") < cleaned_data.get("start_time"):
                        self.add_error(
                            "end_time",
                            forms.ValidationError(
                                _(
                                    "The end of the event can't be before the start of the event"
                                ),
                                code="invalid",
                            ),
                        )
            elif cleaned_data["end_date"] - cleaned_data["start_date"] > timedelta(6):
                self.add_error(
                    "end_date",
                    forms.ValidationError(
                        _(
                            "The maximum duration for events is 7 days. Consider using recurring events if the event is not continuous."
                        ),
                        code="invalid",
                    ),
                )
        # If everything looks good until now, combine the dates and times into timezone-aware datetimes
        if not self.errors:
            tzinfo = zoneinfo.ZoneInfo(self.instance.timezone)
            cleaned_data["start"] = datetime.combine(
                cleaned_data["start_date"],
                cleaned_data["start_time"],
            ).replace(tzinfo=tzinfo)
            cleaned_data["end"] = datetime.combine(
                cleaned_data["end_date"],
                cleaned_data["end_time"],
            ).replace(tzinfo=tzinfo)
            # Also update data to fix the change detection
            self.data = self.data.copy()
            self.data["start"] = cleaned_data["start"]
            self.data["end"] = cleaned_data["end"]
        logger.debug("EventForm validated [2] with cleaned data %r", cleaned_data)
        return cleaned_data
