"""
Form for creating an organization object
"""
from django import forms

from ...models import BedTargetGroup
from ...utils.slug_utils import generate_unique_slug


class BedTargetGroupForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = BedTargetGroup
        fields = ['name', 'slug', 'description']

    def clean_slug(self):
        return generate_unique_slug(self, 'bed_target_group')
