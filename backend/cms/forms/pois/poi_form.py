"""
Form for creating a poi object and poi translation object
"""
import logging

from django import forms

from ...models import POI


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


    # pylint: disable=arguments-differ
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
