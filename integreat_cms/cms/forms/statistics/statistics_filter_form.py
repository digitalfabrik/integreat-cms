"""
Form for submitting filter requests
"""
import logging
from datetime import date, timedelta
from django import forms
from django.utils.translation import ugettext_lazy as _

from ...constants import matomo_periods

logger = logging.getLogger(__name__)


class StatisticsFilterForm(forms.Form):
    """
    Form to filter the statistics graph
    """

    start_date = forms.DateField(
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
        required=True,
        initial=date.today() - timedelta(days=31),
        label=_("From"),
    )
    end_date = forms.DateField(
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
        required=True,
        initial=date.today() - timedelta(days=1),
        label=_("To"),
    )
    period = forms.ChoiceField(
        required=True,
        choices=matomo_periods.CHOICES,
        initial=matomo_periods.DAY,
        label=_("Evaluation"),
    )

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned data
        :rtype: dict
        """
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            # If both dates are given, check if they are valid
            self.add_error(
                "start_date",
                forms.ValidationError(
                    _("The start date can't be after the end date"),
                    code="invalid",
                ),
            )
            self.add_error(
                "end_date",
                forms.ValidationError(
                    _("The end date can't be before the start date"),
                    code="invalid",
                ),
            )

        logger.debug(
            "StatisticsFilterForm validated [2] with cleaned data %r", cleaned_data
        )
        return cleaned_data
