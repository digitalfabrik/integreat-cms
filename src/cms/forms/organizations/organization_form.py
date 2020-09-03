from django import forms

from ...models import Organization


class OrganizationForm(forms.ModelForm):
    """
    Form for creating and modifying organization objects
    """

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "thumbnail",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
