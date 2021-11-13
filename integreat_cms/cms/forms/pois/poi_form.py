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
            "location_not_on_map",
            "icon",
        ]
        #: The widgets which are used in this form
        widgets = {
            "icon": IconWidget(),
        }
