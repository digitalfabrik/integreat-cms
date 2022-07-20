from datetime import date

from django import forms
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from ..custom_filter_form import CustomFilterForm
from ...constants import feedback_ratings, feedback_read_status
from ...models import Feedback, Language


class RegionFeedbackFilterForm(CustomFilterForm):
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

    def apply(self, feedback, region):
        """
        Filter the feedback list according to the given filter data

        :param feedback: The list of feedback
        :type feedback: list

        :param region: The current region
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :return: The filtered feedback list and the search query
        :rtype: tuple
        """
        if not self.is_enabled:
            return feedback, None

        query = self.cleaned_data["query"]
        if query:
            feedback = Feedback.search(region=region, query=query)

        # Filter feedback for region
        if self.cleaned_data.get("region", None):
            feedback = feedback.filter(region=self.cleaned_data["region"])
        # Filter feedback for language
        if self.cleaned_data["language"]:
            feedback = feedback.filter(language=self.cleaned_data["language"])
        # Filter feedback for category
        if self.cleaned_data["category"]:
            # Inherited models automatically get their name as lowercase assigned as reverse relationship from the base class
            filter_condition = self.cleaned_data["category"].lower() + "__isnull"
            feedback = feedback.filter(**{filter_condition: False})
        # Filter feedback for timerange
        feedback = feedback.filter(
            created_date__date__gte=self.cleaned_data["date_from"] or date.min,
            created_date__date__lte=self.cleaned_data["date_to"] or date.max,
        )
        # Filter feedback for their read status (skip filtering if either both or no checkboxes are checked)
        read_status = self.cleaned_data["read_status"]
        if read_status == [feedback_read_status.READ]:
            feedback = feedback.filter(read_by__isnull=False)
        elif read_status == [feedback_read_status.UNREAD]:
            feedback = feedback.filter(read_by__isnull=True)
        # Filter feedback for ratings (skip filtering if either all or no checkboxes are checked)
        if (
            len(self.cleaned_data["rating"]) != len(feedback_ratings.FILTER_CHOICES)
            and len(self.cleaned_data["rating"]) != 0
        ):
            if "" in self.cleaned_data["rating"]:
                feedback_without_rating = feedback.filter(rating__isnull=True)

            feedback = feedback.filter(rating__in=self.cleaned_data["rating"])

            if "" in self.cleaned_data["rating"]:
                feedback = feedback.union(feedback_without_rating)

        return feedback, query
