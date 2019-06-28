"""
Form for creating an organization object
"""

from django import forms
from ...models.organization import Organization


class OrganizationForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = Organization
        fields = ['name', 'slug', 'thumbnail',]

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
