from django import forms
from django.utils.translation import ugettext_lazy as _

from ...constants import translation_status


class PageFilterForm(forms.Form):
    """
    Form for filtering page objects
    """

    translation_status = forms.MultipleChoiceField(
        label=_("Translation status"),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "default-checked"}),
        choices=translation_status.CHOICES,
        initial=[key for (key, val) in translation_status.CHOICES],
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
