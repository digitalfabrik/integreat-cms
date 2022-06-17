import logging

from django import forms
from django.conf import settings
from django.utils.translation import gettext as _

from geopy.distance import distance

from ....nominatim_api.nominatim_api_client import NominatimApiClient
from ...models import POI
from ..custom_model_form import CustomModelForm
from ..icon_widget import IconWidget


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
        ]
        #: The widgets which are used in this form
        widgets = {
            "icon": IconWidget(),
        }

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        # When the Nominatim API is enabled, validate the coordinates
        if settings.NOMINATIM_API_ENABLED:
            nominatim_api_client = NominatimApiClient()
            latitude, longitude = nominatim_api_client.get_coordinates(
                street=cleaned_data.get("address"),
                postalcode=cleaned_data.get("postcode"),
                city=cleaned_data.get("city"),
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
