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
        fields = [
            'code',
            'english_name',
            'native_name',
            'text_direction',
        ]
