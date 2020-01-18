"""
Form for creating a poi object and poi translation object
"""
import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from ...constants import status
from ...models import POITranslation
from ...utils.slug_utils import generate_unique_slug


logger = logging.getLogger(__name__)


class POITranslationForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    PUBLIC_CHOICES = (
        (True, _('Public')),
        (False, _('Private')),
    )

    class Meta:
        model = POITranslation
        fields = ['title', 'short_description', 'status', 'description', 'slug']

    #pylint: disable=too-many-arguments
    def __init__(self, data=None, instance=None, disabled=False, region=None, language=None):
        logger.info('POITranslationForm instantiated with data %s and instance %s', data, instance)

        self.region = region
        self.language = language

        # To set the status value through the submit button, we have to overwrite the field value for status.
        # We could also do this in the save() function, but this would mean that it is not recognized in changed_data.
        # Check if POST data was submitted
        if data:
            # Copy QueryDict because it is immutable
            data = data.copy()
            # Update the POST field with the status corresponding to the submitted button
            if 'submit_draft' in data:
                data.update({'status': status.DRAFT})
            elif 'submit_review' in data:
                data.update({'status': status.REVIEW})
            elif 'submit_public' in data:
                data.update({'status': status.PUBLIC})

        super(POITranslationForm, self).__init__(data=data, instance=instance)

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if disabled:
            for _, field in self.fields.items():
                field.disabled = True

    # pylint: disable=arguments-differ
    def save(self, poi=None, user=None):
        logger.info('POITranslationForm saved with cleaned data %s and changed data %s', self.cleaned_data, self.changed_data)

        poi_translation = super(POITranslationForm, self).save(commit=False)

        if not self.instance.id:
            # only update these values when poi translation is created
            poi_translation.poi = poi
            poi_translation.creator = user
            poi_translation.language = self.language

        # Only create new version if content changed
        if not {'slug', 'title', 'short_description', 'description'}.isdisjoint(self.changed_data):
            poi_translation.version = poi_translation.version + 1
            poi_translation.pk = None
        poi_translation.save()

        return poi_translation

    def clean_slug(self):
        unique_slug = generate_unique_slug(self, 'poi')
        self.data = self.data.copy()
        self.data['slug'] = unique_slug
        return unique_slug
