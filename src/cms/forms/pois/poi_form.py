import logging

from ...models import POI
from ..custom_model_form import CustomModelForm
from ..icon_widget import IconWidget


logger = logging.getLogger(__name__)


class POIForm(CustomModelForm):
    """
    Form for creating and modifying POI objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = POI
        #: The fields of the model which should be handled by this form
        fields = [
            "address",
            "postcode",
            "city",
            "country",
            "latitude",
            "longitude",
            "icon",
        ]
        #: The widgets which are used in this form
        widgets = {
            "icon": IconWidget(),
        }

    def __init__(self, data=None, files=None, instance=None):
        """
        Initialize POI form

        :param data: submitted POST data
        :type data: dict

        :param instance: This form's instance
        :type instance: ~cms.models.pois.poi.POI
        """

        # instantiate ModelForm
        super().__init__(data=data, files=files, instance=instance)

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if instance and instance.archived:
            for _, field in self.fields.items():
                field.disabled = True

    # pylint: disable=arguments-differ
    def save(self, region=None):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param region: The region of this form's POI instance
        :type region: ~cms.models.regions.region.Region

        :return: The saved POI object
        :rtype: ~cms.models.pois.poi.POI
        """

        poi = super().save(commit=False)

        if not self.instance.id:
            # only update these values when poi is created
            poi.region = region

        poi.save()
        return poi
