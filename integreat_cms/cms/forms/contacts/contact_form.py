from __future__ import annotations

import logging
import re

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ...models import Contact
from ..custom_model_form import CustomModelForm

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
            "location": {"invalid_choice": _("Location cannot be empty.")},
        }

    def clean_phone_number(self) -> str:
        """
        Validate the phone number field (see :ref:`overriding-modelform-clean-method`).
        The number will be converted to the international format, i.e. `+XX (X) XXXXXXXX`.

        :return: The reformatted phone number
        """
        phone_number = self.cleaned_data["phone_number"]
        if not phone_number or re.fullmatch(r"^\+\d{2,3} \(0\) \d*$", phone_number):
            return phone_number

        phone_number = re.sub(r"[^0-9+]", "", phone_number)
        prefix = settings.DEFAULT_PHONE_NUMBER_COUNTRY_CODE
        if phone_number.startswith("00"):
            prefix = f"+{phone_number[2:4]}"
            phone_number = phone_number[4:]
        elif phone_number.startswith("0"):
            phone_number = phone_number[1:]
        elif phone_number.startswith("+"):
            prefix = phone_number[0:3]
            phone_number = phone_number[3:]

        return f"{prefix} (0) {phone_number}"
