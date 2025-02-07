from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.utils.translation import gettext_lazy as _

from ...constants import frequency, weekdays
from ...models import RecurrenceRule
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class RecurrenceRuleForm(CustomModelForm):
    """
    Form for creating and modifying event recurrence rule objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = RecurrenceRule
        #: The fields of the model which should be handled by this form
        fields = [
            "frequency",
            "interval",
            "weekdays_for_weekly",
            "weekday_for_monthly",
            "week_for_monthly",
            "recurrence_end_date",
        ]
        #: The widgets which are used in this form
        widgets = {
            "weekdays_for_weekly": forms.SelectMultiple(choices=weekdays.CHOICES),
            "recurrence_end_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
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
                    _("No recurrence frequency selected"),
                    code="required",
                ),
            )
        elif cleaned_data.get("frequency") == frequency.DAILY:
            self.add_error(
                "frequency",
                forms.ValidationError(
                    _('Recurrence "daily" is not allowed anymore'), code="invalid"
                ),
            )
        elif cleaned_data.get("frequency") == frequency.WEEKLY and not cleaned_data.get(
            "weekdays_for_weekly",
        ):
            self.add_error(
                "weekdays_for_weekly",
                forms.ValidationError(
                    _("No weekdays for weekly recurrence selected"),
                    code="required",
                ),
            )
        elif cleaned_data.get("frequency") == frequency.MONTHLY:
            if cleaned_data.get("weekday_for_monthly") is None:
                self.add_error(
                    "weekday_for_monthly",
                    forms.ValidationError(
                        _("No weekday for monthly recurrence selected"),
                        code="required",
                    ),
                )
            if not cleaned_data.get("week_for_monthly"):
                self.add_error(
                    "week_for_monthly",
                    forms.ValidationError(
                        _("No week for monthly recurrence selected"),
                        code="required",
                    ),
                )

        if (
            cleaned_data.get("recurrence_end_date")
            and self.event_start_date
            and cleaned_data.get("recurrence_end_date") <= self.event_start_date
        ):
            self.add_error(
                "recurrence_end_date",
                forms.ValidationError(
                    _("The recurrence end date has to be after the event's start date"),
                    code="invalid",
                ),
            )

        logger.debug(
            "RecurrenceRuleForm validated [2] with cleaned data %r",
            cleaned_data,
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
            self.data,
            self.files,
            self.add_prefix("weekdays_for_weekly"),
        )
        initial = self["weekdays_for_weekly"].initial
        if value:
            value = set(map(int, value))
        if initial:
            initial = set(initial)
        if value != initial:
            self.changed_data.append("weekdays_for_weekly")
        return bool(self.changed_data)
