from django import forms

from ...models import Directory


class DirectoryForm(forms.ModelForm):
    """
    Form for creating and modifying directory objects
    """

    class Meta:
        model = Directory
        fields = ["name"]
