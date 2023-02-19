# @TODO: this class is not used, should be deleted, before merging with dev

from django import forms
# pylint: disable=unused-import
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _
# pylint: disable=unused-import
from ...models import Page, Region

 # pylint: disable=unused-argument, missing-class-docstring
class TranslatePagesForm(forms.Form):
    def __init__(self, languages, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(language, language.translated_name) for language in languages]
        all_languages_choice = (-1, _("Select all"))
        choices.insert(0, (all_languages_choice))
        self.fields["translate_languages"] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple(
                attrs={
                    "class": "justify-between font-normal whitespace-nowrap rounded-b shadow p-2 text-gray-800 hover:bg-gray-200 bg-white"
                }
            ),
            choices=choices,
        )
