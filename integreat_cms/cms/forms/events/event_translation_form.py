import logging

from ...models import EventTranslation
from ..custom_content_model_form import CustomContentModelForm


logger = logging.getLogger(__name__)


class EventTranslationForm(CustomContentModelForm):
    """
    Form for creating and modifying event translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = EventTranslation
        #: The fields of the model which should be handled by this form
        fields = [
            "title",
            "slug",
            "content",
            "status",
            "minor_edit",
        ]
