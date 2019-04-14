"""
Form for creating a language object
"""

from django import forms
from ...models import Language


class LanguageForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = Language
        fields = ['code', 'name', 'text_direction', ]

    def __init__(self, *args, **kwargs):
        super(LanguageForm, self).__init__(*args, **kwargs)

    def save_language(self, language_code=None):
        """Function to create or update a language
            language_code ([String], optional): Defaults to None. If it's not set creates
            a language or update the language with the given code.
        """

        if language_code:
            # save language
            language = Language.objects.get(code=language_code)
            language.code = self.cleaned_data['code']
            language.name = self.cleaned_data['name']
            language.text_direction = self.cleaned_data['text_direction']
            language.save()
        else:
            # create language
            language = Language.objects.create(
                code=self.cleaned_data['code'],
                name=self.cleaned_data['name'],
                text_direction=self.cleaned_data['text_direction'],
            )
