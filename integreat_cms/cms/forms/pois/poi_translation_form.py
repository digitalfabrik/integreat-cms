from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ...models import POITranslation
from ..machine_translation_form import MachineTranslationForm

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class POITranslationForm(MachineTranslationForm):
    """
    Form for creating and modifying POI translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = POITranslation
        #: The fields of the model which should be handled by this form
        fields = MachineTranslationForm.Meta.fields + ["meta_description", "slug"]

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize POI translation form

        :param \**kwargs: The supplied keyword arguments
        """

        # Pop kwarg to make sure the super class does not get this param
        default_language_title = kwargs.pop("default_language_title", None)

        # Instantiate MachineTranslationForm
        super().__init__(**kwargs)

        if default_language_title:
            self.fields["title"].initial = default_language_title
