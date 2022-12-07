from django import forms
from django.utils.translation import gettext_lazy as _

from ...models import Region
from .region_feedback_filter_form import RegionFeedbackFilterForm


class AdminFeedbackFilterForm(RegionFeedbackFilterForm):
    """
    Form for filtering admin (technical) feedback objects
    """

    region = forms.ModelChoiceField(
        Region.objects.all(),
        label=_("Region"),
        empty_label=_("All regions"),
        required=False,
    )
