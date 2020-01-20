"""
Form for creating an organization object
"""
from django import forms

from ...models import BedTargetGroup


class BedTargetGroupForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = BedTargetGroup
        fields = ['name', 'slug', 'description']
