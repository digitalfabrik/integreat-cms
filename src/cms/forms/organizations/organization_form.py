from django import forms

from ...models import Organization


class OrganizationForm(forms.ModelForm):
    """
    Form for creating and modifying organization objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Organization
        #: The fields of the model which should be handled by this form
        fields = [
            "name",
            "slug",
            "thumbnail",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
