from django import forms

from cms.constants import translation_status


class PageFilterForm(forms.Form):
    translation_status = forms.TypedMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "default-checked"}),
        choices=translation_status.CHOICES,
        initial=[key for (key, val) in translation_status.CHOICES],
        coerce=translation_status.DATATYPE,
        required=False,
    )
