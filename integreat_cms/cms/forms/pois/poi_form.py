from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from geopy.distance import distance
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ....nominatim_api.nominatim_api_client import NominatimApiClient
from ...constants import opening_hours, status
from ...models import POI
from ...utils.content_translation_utils import update_links_to
from ...utils.translation_utils import gettext_many_lazy as __
from ..custom_model_form import CustomModelForm
from ..icon_widget import IconWidget

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class POIForm(CustomModelForm):
    """
    Form for creating and modifying POI objects
    """

    #: The distance in km between the manually entered coordinates and the coordinates returned from Nominatim
    nominatim_distance_delta = 0

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = POI
        #: The fields of the model which should be handled by this form
        fields = [
            "address",
            "postcode",
            "city",
            "country",
            "latitude",
            "longitude",
            "location_on_map",
            "icon",
            "website",
            "email",
            "phone_number",
            "category",
            "opening_hours",
            "temporarily_closed",
            "appointment_url",
            "organization",
            "barrier_free",
        ]
        #: The widgets which are used in this form
        widgets = {
            "icon": IconWidget(),
        }

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize page form

        :param \**kwargs: The supplied keyword arguments
        """
        super().__init__(**kwargs)

        self.fields["organization"].queryset = (
            self.instance.region.organizations.filter(archived=False)
        )

    def clean_opening_hours(self) -> list[dict[str, Any]]:
        # pylint: disable=too-many-return-statements
        """
        Validate the opening hours field (see :ref:`overriding-modelform-clean-method`).

        :return: The valid opening hours
        """
        # Only show generic error message because users cannot directly modify the JSON input
        generic_error = __(
            _("An error occurred while saving the opening hours."),
            _("Please contact an administrator."),
        )
        cleaned_opening_hours = self.cleaned_data["opening_hours"]
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
                "Opening hours of %r: JSON does not match schema: %r", self.instance, e
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

    def clean(self) -> dict[str, Any]:
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        """
        cleaned_data = super().clean()

        # When the Nominatim API is enabled, validate the coordinates
        if settings.NOMINATIM_API_ENABLED:
            nominatim_api_client = NominatimApiClient()
            latitude, longitude = nominatim_api_client.get_coordinates(
                street=cleaned_data.get("address", ""),
                postalcode=cleaned_data.get("postcode", ""),
                city=cleaned_data.get("city", ""),
            )
            if latitude and longitude:
                # Only override coordinates if not set manually
                if not cleaned_data.get("latitude"):
                    cleaned_data["latitude"] = latitude
                if not cleaned_data.get("longitude"):
                    cleaned_data["longitude"] = longitude
                # Store distance between manually entered coordinates and API result
                self.nominatim_distance_delta = int(
                    distance(
                        (cleaned_data["latitude"], cleaned_data["longitude"]),
                        (latitude, longitude),
                    ).km
                )

        if cleaned_data.get("location_on_map"):
            # If the location should be shown on the map, require the coordinates
            if not cleaned_data.get("latitude"):
                self.add_error(
                    "latitude",
                    forms.ValidationError(
                        _(
                            "Could not derive the coordinates from the address, please fill "
                            "the field manually if the location is to be displayed on the map."
                        ),
                        code="required",
                    ),
                )
            if not cleaned_data.get("longitude"):
                self.add_error(
                    "longitude",
                    forms.ValidationError(
                        _(
                            "Could not derive the coordinates from the address, please fill "
                            "the field manually if the location is to be displayed on the map."
                        ),
                        code="required",
                    ),
                )

        return cleaned_data

    def save(self, commit: bool = True) -> Any:
        result = super().save(commit)

        # Update links to instances of this poi, since the autogenerated data might contain a link
        if commit and "icon" in self.changed_data:
            logger.debug("Updating links to %r, since its icon changed", self.instance)
            for (
                translation
            ) in self.instance.prefetched_public_translations_by_language_slug.values():
                if translation.status == status.PUBLIC:
                    update_links_to(translation, translation.creator)

        return result
