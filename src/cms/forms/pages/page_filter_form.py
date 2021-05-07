from django import forms

from cms.constants import translation_status


class PageFilterForm(forms.Form):
    """
    Form for filtering page objects
    """

    translation_status = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "default-checked"}),
        choices=translation_status.CHOICES,
        initial=[key for (key, val) in translation_status.CHOICES],
        required=False,
    )
