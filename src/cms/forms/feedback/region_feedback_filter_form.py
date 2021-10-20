from django import forms
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from ...constants import feedback_ratings, feedback_read_status
from ...models import Feedback, Language


class RegionFeedbackFilterForm(forms.Form):
    """
    Form for filtering feedback objects
    """

    language = forms.ModelChoiceField(
        Language.objects.all(),
        label=_("Language"),
        empty_label=_("All languages"),
        required=False,
    )
    category = forms.ChoiceField(
        choices=[("", _("All categories"))]
        + [
            (submodel.__name__, capfirst(submodel._meta.verbose_name))
            for submodel in Feedback.__subclasses__()
        ],
        label=_("Category"),
        required=False,
    )
    read_status = forms.MultipleChoiceField(
        label=_("Status"),
        widget=forms.CheckboxSelectMultiple(),
        choices=feedback_read_status.CHOICES,
        initial=feedback_read_status.INITIAL,
        required=False,
    )
    rating = forms.MultipleChoiceField(
        label=_("Rating"),
        widget=forms.CheckboxSelectMultiple(),
        choices=feedback_ratings.FILTER_CHOICES,
        initial=feedback_ratings.INITIAL,
        required=False,
    )
    date_from = forms.DateField(
        label=_("From"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "default-value", "data-default-value": ""},
        ),
        required=False,
    )
    date_to = forms.DateField(
        label=_("To"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "default-value", "data-default-value": ""},
        ),
        required=False,
    )
    query = forms.CharField(required=False)

    def filters_visible(self):
        """
        This function determines whether the filter form is visible by default.

        :return: whether any filters (other than search were changed)
        :rtype: bool
        """
        return self.has_changed() and self.changed_data != ["query"]
