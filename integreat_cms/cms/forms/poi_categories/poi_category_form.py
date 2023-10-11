from __future__ import annotations

import logging

from ...models import POICategory
from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class POICategoryForm(CustomModelForm):
    """
    Form for creating and modifying POICategory objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = POICategory
        #: The fields of the model which should be handled by this form
        fields = [
            "icon",
            "color",
        ]
