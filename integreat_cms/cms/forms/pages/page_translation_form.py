from __future__ import annotations

import logging

from ...models import PageTranslation
from ..machine_translation_form import MachineTranslationForm

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class PageTranslationForm(MachineTranslationForm):
    """
    Form for creating and modifying page translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = PageTranslation
        #: The fields of the model which should be handled by this form
        fields = MachineTranslationForm.Meta.fields + [
            "slug",
            "hix_score",
            "hix_feedback",
        ]
