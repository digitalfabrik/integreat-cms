from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.utils.translation import gettext_lazy as _

from ...models import Contact
from ...utils.link_utils import format_phone_number
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
            "area_of_responsibility",
            "name",
            "location",
            "email",
            "phone_number",
            "mobile_phone_number",
            "website",
        ]

        error_messages = {
            "location": {"invalid_choice": _("Location cannot be empty.")},
        }

    def clean(self) -> dict[str, Any]:
        """
        Validate the selected location, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        """

        cleaned_data = super().clean()

        if (location := cleaned_data.get("location")) and location.archived:
            self.add_error(
                "location",
                forms.ValidationError(
                    _(
                        "An archived location cannot be used for contacts.",
                    ),
                    code="invalid",
                ),
            )
        return cleaned_data

    def clean_phone_number(self) -> str:
        """
        Validate the phone number field (see :ref:`overriding-modelform-clean-method`).
        The number will be converted to the international format, i.e. `+XX (X) XXXXXXXX`.

        :return: The reformatted phone number
        """
        phone_number = self.cleaned_data["phone_number"]
        return format_phone_number(phone_number)

    def clean_mobile_phone_number(self) -> str:
        """
        Validate the mobile phone number field (see :ref:`overriding-modelform-clean-method`).
        The number will be converted to the international format, i.e. `+XX (X) XXXXXXXX`.

        :return: The reformatted phone number
        """
        mobile_phone_number = self.cleaned_data["mobile_phone_number"]
        return format_phone_number(mobile_phone_number)
