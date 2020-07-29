from django import forms

from ...models import Document


class DocumentForm(forms.ModelForm):
    """
    Form for creating and modifying document objects
    """

    class Meta:
        model = Document
        fields = ('description', 'document', )
