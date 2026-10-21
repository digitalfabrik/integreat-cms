from __future__ import annotations

import csv
import json
import logging
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.utils import translation

from ....cms.constants import placecategory, status
from ....cms.forms import PlaceForm, PlaceTranslationForm
from ....cms.models import Language, PlaceCategory, PlaceCategoryTranslation, Region
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
    Management command to import places from CSV
    """

    help = "Import places from CSV"

    def get_or_create_default_category(
        self, default_language: Language
    ) -> PlaceCategory:
        """
        Get the default place category or create if not exists

        :param default_language: The default language of the current region
        :returns: The default place category
        """
        if not (
            default_category := PlaceCategory.objects.filter(
                icon=placecategory.OTHER,
            ).first()
        ):
            default_category = PlaceCategory.objects.create(
                icon=placecategory.OTHER,
                color=placecategory.DARK_BLUE,
            )
            PlaceCategoryTranslation.objects.create(
                category=default_category,
                language=default_language,
                name=placecategory.OTHER,
            )
        return default_category

    def get_category(
        self,
        category_name: str,
        default_language: Language,
    ) -> PlaceCategory:
        """
        Get a place category object from the category's name

        :param category_name: The translated name of the category
        :param default_language: The default language of the current region
        :returns: The given place category
        """
        if category_translation := PlaceCategoryTranslation.objects.filter(
            name=category_name,
        ).first():
            return category_translation.category
        return self.get_or_create_default_category(default_language)

    def autocomplete_address(self, place: dict) -> dict:
        """
        Fill in missing address details

        :param place: The input place dict
        :returns: The updated place dict
        """

        nominatim_api_client = NominatimApiClient()

        result = nominatim_api_client.search(
            street=place["street_address"],
            postalcode=place["postal_code"],
            city=place["city"],
            addressdetails=True,
        )

        if not result:
            return place

        address = result.raw.get("address", {})

        if not place["postal_code"]:
            place["postal_code"] = address.get("postcode")
        if not place["city"]:
            place["city"] = (
                address.get("city") or address.get("town") or address.get("village")
            )
        if not place["country"]:
            place["country"] = address.get("country")
        if not place["longitude"]:
            place["longitude"] = address.get("longitude")
        if not place["latitude"]:
            place["latitude"] = address.get("latitude")

        return place

    def get_opening_hours(self, place: dict) -> list:
        """
        Parse the opening hour columns into our JSON structure

        :param place: The input place dict
        :returns: The opening hour list
        """
        return [
            {
                "timeSlots": (
                    [{"start": place[f"{day}_start"], "end": place[f"{day}_end"]}]
                    if place[f"{day}_start"] and place[f"{day}_end"]
                    else []
                ),
                "allDay": strtobool(place[f"{day}_all_day"]),
                "closed": (
                    strtobool(place[f"{day}_closed"])
                    if place[f"{day}_closed"]
                    else not (
                        place[f"{day}_start"]
                        or place[f"{day}_end"]
                        or place[f"{day}_all_day"]
                        or place[f"{day}_appointment_only"]
                    )
                ),
                "appointmentOnly": strtobool(place[f"{day}_appointment_only"]),
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
            "region_slug",
            help="Import the place objects into this region",
        )
        parser.add_argument("username", help="The username of the creator")

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
        :param region_slug: Import the place objects into this region
        :param username: The username of the creator
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        self.set_logging_stream()

        try:
            region = Region.objects.get(slug=region_slug)
        except Region.DoesNotExist as e:
            raise CommandError(
                f'Region with slug "{region_slug}" does not exist.',
            ) from e

        try:
            user = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist as e:
            raise CommandError(
                f'User with username "{username}" does not exist.',
            ) from e

        with open(csv_filename, newline="", encoding="utf-8") as csv_file:
            places = csv.DictReader(csv_file)
            for place in places:
                place = self.autocomplete_address(place)  # noqa: PLW2901

                data = {
                    "title": place["name"],
                    "address": place["street_address"],
                    "postcode": place["postal_code"],
                    "city": place["city"],
                    "country": place["country"],
                    "longitude": place["longitude"],
                    "latitude": place["latitude"],
                    "place_on_map": strtobool(place["place_on_map"]),
                    "status": status.DRAFT,
                    "opening_hours": json.dumps(self.get_opening_hours(place)),
                    "temporarily_closed": strtobool(place["temporarily_closed"]),
                    "category": self.get_category(
                        place["category"],
                        region.default_language,
                    ).id,
                    "primary_website": place["website"],
                    "appointment_url": place["appointment_url"],
                    "primary_email": place["email"],
                    "primary_phone_number": place["phone_number"],
                    "barrier_free": strtobool(place["barrier_free"]),
                }
                place_form = PlaceForm(
                    data=data,
                    additional_instance_attributes={
                        "region": region,
                    },
                )
                place_translation_form = PlaceTranslationForm(
                    language=region.default_language,
                    data=data,
                    additional_instance_attributes={
                        "creator": user,
                        "language": region.default_language,
                        "place": place_form.instance,
                    },
                    changed_by_user=user,
                )

                with translation.override("en"):
                    if not place_form.is_valid():
                        raise CommandError(
                            "\n\t• "
                            + "\n\t• ".join(
                                m["text"] for m in place_form.get_error_messages()
                            ),
                        )
                    if not place_translation_form.is_valid():
                        raise CommandError(
                            "\n\t• "
                            + "\n\t• ".join(
                                m["text"]
                                for m in place_translation_form.get_error_messages()
                            ),
                        )
                # Save forms
                place_translation_form.instance.place = place_form.save()
                place_translation_form.save()
                logger.success("Imported %r", place_form.instance)  # type: ignore[attr-defined]
        logger.success("✔ Imported CSV file %s", csv_filename)  # type: ignore[attr-defined]
