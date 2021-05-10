from django import forms
from django.utils.translation import ugettext_lazy as _

from cms.constants import translation_status


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
