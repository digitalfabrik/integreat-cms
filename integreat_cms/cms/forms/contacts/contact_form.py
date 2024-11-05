from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from ...models import Contact
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class ContactForm(CustomModelForm):
    """
    Form for creating and modifying contact objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Contact
        #: The fields of the model which should be handled by this form
        fields = [
            "point_of_contact_for",
            "name",
            "location",
            "email",
            "phone_number",
            "website",
        ]

        error_messages = {
            "location": {"invalid_choice": _("Location cannot be empty.")}
        }
