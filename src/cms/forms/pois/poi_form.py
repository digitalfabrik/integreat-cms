import logging

from django import forms

from ...models import POI


logger = logging.getLogger(__name__)


class POIForm(forms.ModelForm):
    """
    Form for creating and modifying POI objects
    """

    class Meta:
        model = POI
        fields = ['address', 'postcode', 'city', 'country', 'latitude', 'longitude']

    def __init__(self, data=None, instance=None):
        logger.info('POIForm instantiated with data %s and instance %s', data, instance)

        # instantiate ModelForm
        super(POIForm, self).__init__(data=data, instance=instance)

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if instance and instance.archived:
            for _, field in self.fields.items():
                field.disabled = True

    # pylint: disable=arguments-differ
    def save(self, region=None):
        logger.info('POIForm saved with cleaned data %s and changed data %s', self.cleaned_data, self.changed_data)

        poi = super(POIForm, self).save(commit=False)

        if not self.instance.id:
            # only update these values when poi is created
            poi.region = region

        poi.save()
        return poi
