from __future__ import annotations

import csv
import json
import logging
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.utils import translation

from ....cms.constants import poicategory, status
from ....cms.forms import POIForm, POITranslationForm
from ....cms.models import Language, POICategory, POICategoryTranslation, Region
from ....core.utils.strtobool import strtobool as strtobool_util
from ....nominatim_api.nominatim_api_client import NominatimApiClient
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


def strtobool(val: str) -> bool:
    """
    A slightly adapted variant of ``strtobool`` which treats an empty string as false

    :param val: The value as string
    :return: The value as boolean
    """
    return strtobool_util(val) if val else False


class Command(LogCommand):
    """
    Management command to import POIs from CSV
    """

    help = "Import POIs from CSV"

    def get_or_create_default_category(self, default_language: Language) -> POICategory:
        """
        Get the default POI category or create if not exists

        :param default_language: The default language of the current region
        :returns: The default POI category
        """
        if not (
            default_category := POICategory.objects.filter(
                icon=poicategory.OTHER
            ).first()
        ):
            default_category = POICategory.objects.create(
                icon=poicategory.OTHER,
                color=poicategory.DARK_BLUE,
            )
            POICategoryTranslation.objects.create(
                category=default_category,
                language=default_language,
                name=poicategory.OTHER,
            )
        return default_category

    def get_category(
        self, category_name: str, default_language: Language
    ) -> POICategory:
        """
        Get a POI category object from the category's name

        :param category_name: The translated name of the category
        :param default_language: The default language of the current region
        :returns: The given POI category
        """
        if category_translation := POICategoryTranslation.objects.filter(
            name=category_name
        ).first():
            return category_translation.category
        return self.get_or_create_default_category(default_language)

    def autocomplete_address(self, poi: dict) -> dict:
        """
        Fill in missing address details

        :param poi: The input POI dict
        :returns: The updated POI dict
        """

        nominatim_api_client = NominatimApiClient()

        result = nominatim_api_client.search(
            street=poi["street_address"],
            postalcode=poi["postal_code"],
            city=poi["city"],
            addressdetails=True,
        )

        if not result:
            return poi

        address = result.raw.get("address", {})

        if not poi["postal_code"]:
            poi["postal_code"] = address.get("postcode")
        if not poi["city"]:
            poi["city"] = (
                address.get("city") or address.get("town") or address.get("village")
            )
        if not poi["country"]:
            poi["country"] = address.get("country")
        if not poi["longitude"]:
            poi["longitude"] = address.get("longitude")
        if not poi["latitude"]:
            poi["latitude"] = address.get("latitude")

        return poi

    def get_opening_hours(self, poi: dict) -> list:
        """
        Parse the opening hour columns into our JSON structure

        :param poi: The input POI dict
        :returns: The opening hour list
        """
        return [
            {
                "timeSlots": (
                    [{"start": poi[f"{day}_start"], "end": poi[f"{day}_end"]}]
                    if poi[f"{day}_start"] and poi[f"{day}_end"]
                    else []
                ),
                "allDay": strtobool(poi[f"{day}_all_day"]),
                "closed": (
                    strtobool(poi[f"{day}_closed"])
                    if poi[f"{day}_closed"]
                    else not (
                        poi[f"{day}_start"]
                        or poi[f"{day}_end"]
                        or poi[f"{day}_all_day"]
                        or poi[f"{day}_appointment_only"]
                    )
                ),
                "appointmentOnly": strtobool(poi[f"{day}_appointment_only"]),
            }
            for day in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
        ]

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument("csv_filename", help="The source CSV file to import from")
        parser.add_argument(
            "region_slug", help="Import the POI objects into this region"
        )
        parser.add_argument("username", help="The username of the creator")

    # pylint: disable=arguments-differ
    def handle(
        self,
        *args: Any,
        csv_filename: str,
        region_slug: str,
        username: str,
        **options: Any,
    ) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param csv_filename: The source CSV file to import from
        :param region_slug: Import the POI objects into this region
        :param username: The username of the creator
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        self.set_logging_stream()

        try:
            region = Region.objects.get(slug=region_slug)
        except Region.DoesNotExist as e:
            raise CommandError(
                f'Region with slug "{region_slug}" does not exist.'
            ) from e

        try:
            user = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist as e:
            raise CommandError(
                f'User with username "{username}" does not exist.'
            ) from e

        with open(csv_filename, newline="", encoding="utf-8") as csv_file:
            pois = csv.DictReader(csv_file)
            for poi in pois:
                poi = self.autocomplete_address(poi)  # noqa: PLW2901

                data = {
                    "title": poi["name"],
                    "address": poi["street_address"],
                    "postcode": poi["postal_code"],
                    "city": poi["city"],
                    "country": poi["country"],
                    "longitude": poi["longitude"],
                    "latitude": poi["latitude"],
                    "location_on_map": strtobool(poi["location_on_map"]),
                    "status": status.DRAFT,
                    "opening_hours": json.dumps(self.get_opening_hours(poi)),
                    "temporarily_closed": strtobool(poi["temporarily_closed"]),
                    "category": self.get_category(
                        poi["category"], region.default_language
                    ).id,
                    "website": poi["website"],
                    "appointment_url": poi["appointment_url"],
                    "email": poi["email"],
                    "phone_number": poi["phone_number"],
                    "barrier_free": strtobool(poi["barrier_free"]),
                }
                poi_form = POIForm(
                    data=data,
                    additional_instance_attributes={
                        "region": region,
                    },
                )
                poi_translation_form = POITranslationForm(
                    language=region.default_language,
                    data=data,
                    additional_instance_attributes={
                        "creator": user,
                        "language": region.default_language,
                        "poi": poi_form.instance,
                    },
                    changed_by_user=user,
                )

                with translation.override("en"):
                    if not poi_form.is_valid():
                        raise CommandError(
                            "\n\t• "
                            + "\n\t• ".join(
                                m["text"] for m in poi_form.get_error_messages()
                            )
                        )
                    if not poi_translation_form.is_valid():
                        raise CommandError(
                            "\n\t• "
                            + "\n\t• ".join(
                                m["text"]
                                for m in poi_translation_form.get_error_messages()
                            )
                        )
                # Save forms
                poi_translation_form.instance.poi = poi_form.save()
                poi_translation_form.save(foreign_form_changed=poi_form.has_changed())
                logger.success("Imported %r", poi_form.instance)  # type: ignore[attr-defined]
        logger.success("✔ Imported CSV file %s", csv_filename)  # type: ignore[attr-defined]
