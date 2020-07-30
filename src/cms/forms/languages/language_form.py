from django import forms

from ...models import Language


class LanguageForm(forms.ModelForm):
    """
    Form for creating and modifying language objects
    """

    class Meta:
        model = Language
        fields = [
            "code",
            "english_name",
            "native_name",
            "text_direction",
        ]
