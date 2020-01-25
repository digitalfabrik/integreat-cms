"""
Form for changing the general bed capacity in a accommodation
"""
import logging

from django import forms

from ...models import Beds



logger = logging.getLogger(__name__)


class BedsGeneralCreationForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = Beds
        fields = [
            'num_beds',
            'num_free_beds'
        ]

    # pylint: disable=arguments-differ
    def save(self, region=None):
        logger.info('BedsGeneralCreationForm saved with cleaned data %s and changed data %s', self.cleaned_data, self.changed_data)
        beds = super(BedsGeneralCreationForm, self).save()
        return beds

