from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

from attr import dataclass
from dateutil import rrule
from django import forms
from django.utils.translation import gettext_lazy as _

from ...constants import frequency, weekdays, weeks
from ...models import RecurrenceRule
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class RecurrenceRuleForm(CustomModelForm):
    """
    Form for creating and modifying event recurrence rule objects
    """

    has_recurrence_end_date = forms.BooleanField(
        required=False, label=_("Recurrence ends")
    )
    frequency = forms.ChoiceField(
        initial=frequency.WEEKLY,
        choices=frequency.CHOICES,
        label=_("frequency"),
        help_text=_("How often the event recurs"),
    )
    interval = forms.IntegerField(
        initial=1,
        min_value=1,
        label=_("Repeat every ... time(s)"),
        help_text=_("The interval in which the event recurs."),
    )
    weekdays_for_weekly = forms.MultipleChoiceField(
        required=False,
        choices=weekdays.CHOICES,
        widget=forms.SelectMultiple(choices=weekdays.CHOICES),
        label=_("weekdays"),
        help_text=_(
            "If the frequency is weekly, this field determines on which days the event takes place"
        ),
    )
    weekday_for_monthly = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + weekdays.CHOICES,
        label=_("weekday"),
        help_text=_(
            "If the frequency is monthly, this field determines on which days the event takes place"
        ),
    )
    week_for_monthly = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + weeks.CHOICES,
        label=_("week"),
        help_text=_(
            "If the frequency is monthly, this field determines on which week of the month the event takes place"
        ),
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = RecurrenceRule
        #: The fields of the model which should be handled by this form
        fields = [
            "recurrence_end_date",
        ]
        #: The widgets which are used in this form
        widgets = {
            "recurrence_end_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}
            ),
        }

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize recurrence rule form

        :param \**kwargs: The supplied keyword arguments
        """

        # Set event start date to be used in clean()-method
        self.event_start_date = kwargs.pop("event_start_date", None)

        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        if self.instance.id:
            # Initialize BooleanField based on RecurrenceRule properties
            self.fields["has_recurrence_end_date"].initial = bool(
                self.instance.recurrence_end_date
            )

            rule = self.instance.to_ical_rrule()
            # self.fields["frequency"].initial = rule.

    def clean(self) -> dict[str, Any]:
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        """
        cleaned_data = super().clean()

        if not cleaned_data.get("frequency"):
            self.add_error(
                "frequency",
                forms.ValidationError(
                    _("No recurrence frequency selected"), code="required"
                ),
            )
        elif cleaned_data.get("frequency") == frequency.WEEKLY and not cleaned_data.get(
            "weekdays_for_weekly"
        ):
            self.add_error(
                "weekdays_for_weekly",
                forms.ValidationError(
                    _("No weekdays for weekly recurrence selected"), code="required"
                ),
            )
        elif cleaned_data.get("frequency") == frequency.MONTHLY:
            if cleaned_data.get("weekday_for_monthly") is None:
                self.add_error(
                    "weekday_for_monthly",
                    forms.ValidationError(
                        _("No weekday for monthly recurrence selected"), code="required"
                    ),
                )
            if not cleaned_data.get("week_for_monthly"):
                self.add_error(
                    "week_for_monthly",
                    forms.ValidationError(
                        _("No week for monthly recurrence selected"), code="required"
                    ),
                )

        if cleaned_data.get("has_recurrence_end_date"):
            if not cleaned_data.get("recurrence_end_date"):
                self.add_error(
                    "recurrence_end_date",
                    forms.ValidationError(
                        _(
                            "If the recurrence ends, the recurrence end date is required"
                        ),
                        code="required",
                    ),
                )
            elif (
                self.event_start_date
                and cleaned_data.get("recurrence_end_date") <= self.event_start_date
            ):
                self.add_error(
                    "recurrence_end_date",
                    forms.ValidationError(
                        _(
                            "The recurrence end date has to be after the event's start date"
                        ),
                        code="invalid",
                    ),
                )
        else:
            cleaned_data["recurrence_end_date"] = None

        logger.debug(
            "RecurrenceRuleForm validated [2] with cleaned data %r", cleaned_data
        )
        return cleaned_data

    def has_changed(self) -> bool:
        """
        This function provides a workaround for the ``weekdays_for_weekly`` field to be correctly recognized as changed.

        :return: Whether or not the recurrence rule form has changed
        """
        # Handle weekdays_for_weekly data separately from the other data because has_changed doesn't work
        # with CheckboxSelectMultiple widgets and ArrayFields out of the box
        try:
            # Have to remove the corresponding field name from self.changed_data
            self.changed_data.remove("weekdays_for_weekly")
        except ValueError:
            return super().has_changed()
        value = self.fields["weekdays_for_weekly"].widget.value_from_datadict(
            self.data, self.files, self.add_prefix("weekdays_for_weekly")
        )
        initial = self["weekdays_for_weekly"].initial
        if value:
            value = set(map(int, value))
        if initial:
            initial = set(initial)
        if value != initial:
            self.changed_data.append("weekdays_for_weekly")
        return bool(self.changed_data)


@dataclass
class FormRecurrenceRule:
    frequency: int
    interval: int
    weekdays_for_weekly: list[int] | None
    weekday_for_monthly: int | None
    week_for_monthly: int | None

    @classmethod
    def from_ical_rrule(cls, rule: rrule.rrule) -> Self:
        ical_freq_to_form_freq = {
            rrule.YEARLY: frequency.YEARLY,
            rrule.MONTHLY: frequency.MONTHLY,
            rrule.WEEKLY: frequency.WEEKLY,
            rrule.DAILY: frequency.DAILY,
        }
        return FormRecurrenceRule(frequency=ical_freq_to_form_freq[rule._freq])
