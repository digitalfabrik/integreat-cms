import logging

from ..custom_model_form import CustomModelForm
from ...models import MediaFile

logger = logging.getLogger(__name__)


class MediaFileForm(CustomModelForm):
    """
    Form for modifying media file objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = MediaFile
        #: The fields of the model which should be handled by this form
        fields = (
            "name",
            "alt_text",
        )
