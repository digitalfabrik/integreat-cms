import logging

from ...models import Region
from ..custom_model_form import CustomModelForm


logger = logging.getLogger(__name__)


class TranslationsManagementForm(CustomModelForm):
    """
    Form for modifying machine translation settings of a region
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class,
        see the :class:`django.forms.ModelForm` for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Region
        #: The fields of the model which should be handled by this form
        fields = [
            "machine_translate_pages",
            "machine_translate_events",
            "machine_translate_pois",
        ]
