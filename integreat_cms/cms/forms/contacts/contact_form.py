from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django import forms
from django.utils.translation import gettext_lazy as _
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ...constants import opening_hours
from ...models import Contact
from ...utils.link_utils import format_phone_number
from ...utils.translation_utils import gettext_many_lazy as __
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class ContactForm(CustomModelForm):
    """
    Form for creating and modifying contact objects
    """

    use_location_opening_hours = forms.BooleanField(
        required=False, label=_("Adopt opening hours from linked location")
    )

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
            "opening_hours",
            "appointment_url",
        ]

        error_messages = {
            "location": {"invalid_choice": _("Location cannot be empty.")},
        }

    def __init__(self, **kwargs: Any) -> None:
        self.request = kwargs.pop("request", None)
        adopt_hours = True
        instance = kwargs.get("instance")
        if instance and instance.id:
            adopt_hours = instance.opening_hours is None
            if adopt_hours:
                instance.opening_hours = instance.location.opening_hours
        super().__init__(**kwargs)
        self.fields["use_location_opening_hours"].initial = adopt_hours

    def clean(self) -> dict[str, Any]:
        """
        Validate the selected location, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        """

        cleaned_data = super().clean()
        self.cleaned_data["opening_hours"] = self.validate_opening_hours()

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

    def validate_opening_hours(self) -> list[dict[str, Any]] | None:
        """
        Validate the opening hours field (see :ref:`overriding-modelform-clean-method`).

        :return: The valid opening hours
        """
        # Remove when opening hours become available for all users
        if not self.request.user.has_perm("cms.test_beta_features"):
            return None

        if self.cleaned_data["use_location_opening_hours"]:
            return None

        # Only show generic error message because users cannot directly modify the JSON input
        generic_error = __(
            _("An error occurred while saving the opening hours."),
            _("Please contact an administrator."),
        )
        cleaned_opening_hours = self.cleaned_data["opening_hours"]

        # Remove when opening hours become available for all users or after implementing opening hours for the ajax contact form too
        if cleaned_opening_hours is None:
            return None

        # If a string is given, try to load as JSON string
        if isinstance(cleaned_opening_hours, str):
            try:
                cleaned_opening_hours = json.loads(cleaned_opening_hours)
            except json.JSONDecodeError:
                logger.warning(
                    "Opening hours of %r: No valid JSON: %r",
                    self.instance,
                    cleaned_opening_hours,
                )
                self.add_error("opening_hours", generic_error)
                return cleaned_opening_hours
        # Check whether input matches the given schema
        try:
            validate(
                instance=cleaned_opening_hours,
                schema=opening_hours.JSON_SCHEMA,
            )
        except ValidationError as e:
            logger.warning(
                "Opening hours of %r: JSON does not match schema: %r",
                self.instance,
                e,
            )
            self.add_error("opening_hours", generic_error)
            return cleaned_opening_hours
        # Validate each day
        for index, day in enumerate(cleaned_opening_hours):
            # Check for invalid combinations
            if day["allDay"] and day["closed"]:
                logger.warning(
                    "Opening hours of %r: Day %s is both open all day and closed",
                    self.instance,
                    index,
                )
                self.add_error("opening_hours", generic_error)
                return cleaned_opening_hours
            if (day["allDay"] or day["closed"]) and len(day["timeSlots"]) > 0:
                logger.warning(
                    "Opening hours of %r: Day %s is open all day or closed, but has time slots",
                    self.instance,
                    index,
                )
                self.add_error("opening_hours", generic_error)
                return cleaned_opening_hours
            if not (day["allDay"] or day["closed"]) and not day["timeSlots"]:
                logger.warning(
                    "Opening hours of %r: Day %s is neither open all day nor closed, but has no time slots",
                    self.instance,
                    index,
                )
                self.add_error("opening_hours", generic_error)
                return cleaned_opening_hours
            # Validate time slots
            for slot_index, time_slot in enumerate(day["timeSlots"]):
                if time_slot["start"] >= time_slot["end"]:
                    logger.warning(
                        "Opening hours of %r: Time slot %s of day %s ends before it starts",
                        self.instance,
                        slot_index,
                        index,
                    )
                    self.add_error("opening_hours", generic_error)
                    return cleaned_opening_hours
                if (
                    slot_index > 0
                    and time_slot["start"] <= day["timeSlots"][slot_index - 1]["end"]
                ):
                    logger.warning(
                        "Opening hours of %r: Time slot %s of day %s starts before the previous ends",
                        self.instance,
                        slot_index,
                        index,
                    )
                    self.add_error("opening_hours", generic_error)
                    return cleaned_opening_hours
        return cleaned_opening_hours

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
