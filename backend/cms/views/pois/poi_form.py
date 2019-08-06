"""
Form for creating a poi object and poi translation object
"""

import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from ...models import POI, POITranslation
from ..utils.slug_utils import generate_unique_slug

logger = logging.getLogger(__name__)


class POIForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = POI
        fields = ['address', 'postcode', 'city', 'country', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):

        logger.info(
            'New POIForm instantiated with args %s and kwargs %s',
            args,
            kwargs
        )

        # pop kwarg to make sure the super class does not get this param
        self.region = kwargs.pop('region', None)

        # instantiate ModelForm
        super(POIForm, self).__init__(*args, **kwargs)


    # pylint: disable=W0221
    def save(self, *args, **kwargs):

        logger.info(
            'POIForm saved with args %s and kwargs %s',
            args,
            kwargs
        )

        # don't commit saving of ModelForm, because required fields are still missing
        kwargs['commit'] = False
        poi = super(POIForm, self).save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when poi is created
            poi.region = self.region
        poi.save()
        return poi


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
        fields = ['title', 'status', 'description', 'slug', 'public']

    def __init__(self, *args, **kwargs):

        logger.info(
            'New POITranslationForm with args %s and kwargs %s',
            args,
            kwargs
        )

        # pop kwarg to make sure the super class does not get this param
        self.region = kwargs.pop('region', None)
        self.language = kwargs.pop('language', None)

        super(POITranslationForm, self).__init__(*args, **kwargs)

        self.fields['public'].widget = forms.Select(choices=self.PUBLIC_CHOICES)

    # pylint: disable=W0221
    def save(self, *args, **kwargs):

        logger.info(
            'POITranslationForm saved with args %s and kwargs %s',
            args,
            kwargs
        )

        # pop kwarg to make sure the super class does not get this param
        poi = kwargs.pop('poi', None)
        user = kwargs.pop('user', None)

        if not self.instance.id:
            # don't commit saving of ModelForm, because required fields are still missing
            kwargs['commit'] = False

        poi_translation = super(POITranslationForm, self).save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when poi translation is created
            poi_translation.poi = poi
            poi_translation.creator = user
            poi_translation.language = self.language

        poi_translation.save()

        return poi_translation

    def clean_slug(self):
        return generate_unique_slug(self, 'poi')
