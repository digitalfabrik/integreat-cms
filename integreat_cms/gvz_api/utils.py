"""
Helper classes for Gemeindeverzeichnis API
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import requests
from django.conf import settings

from ..cms.constants import administrative_division as ad

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class GvzApiWrapper:
    """
    Class that wraps around the GVZ (Gemeindeverzeichnis) API
    """

    api_url: str = settings.GVZ_API_URL
    """
    The URL to the external GVZ API
    """

    def search(
        self, region_name: str | None, division_category: int | None
    ) -> list[dict[str, Any]]:
        """
        Search for a region and return candidates

        :param region_name: name of a region (city name, county name, etc)
        :param division_category: GVZ category of division (state, district, county, municipality)
        :return: JSON search results defined in the GVZ API
        """
        logger.debug("Searching for %r", region_name)
        regions = requests.get(
            f"{self.api_url}/api/administrative_divisions/?search={region_name}&division_category={division_category}",
            timeout=settings.DEFAULT_REQUEST_TIMEOUT,
        ).json()["results"]
        return regions

    def get_details(self, ags: str) -> dict | None:
        """
        Get details for a region id (i.e. Gemeindeschlüssel)

        :param ags: Gemeindeschlüssel
        :return: dictionary containing longitude, latitude, type, id, name
        """
        logger.debug("GVZ API: Details for %r", ags)
        result = requests.get(
            f"{self.api_url}/api/administrative_divisions/?ags={ags}",
            timeout=settings.DEFAULT_REQUEST_TIMEOUT,
        ).json()
        if result["count"] != 1:
            return None
        region = result["results"][0]
        if "," in region["name"]:
            region["name"] = region["name"].split(",")[0]
        return {
            "id": region["id"],
            "ags": region["ags"],
            "name": region["name"],
            "longitude": region["longitude"],
            "latitude": region["latitude"],
            "type": region["division_type"],
            "children": region["children"],
        }

    def get_child_coordinates(self, child_urls: list) -> dict:
        """
        Recursively get coordinates for list of children

        :param child_urls: URLs to REST API children
        :return: dictionary of coordinates
        """
        result = {}
        for url in child_urls:
            response = requests.get(
                url, timeout=settings.DEFAULT_REQUEST_TIMEOUT
            ).json()
            result[response["name"]] = {
                "longitude": response["longitude"],
                "latitude": response["latitude"],
            }
            result.update(self.get_child_coordinates(response["children"]))
        return result

    @staticmethod
    def translate_division_category(division_type: str | None) -> int | None:
        """
        Map Integreat CMS division types to Gemeindeverzeichnis division categories.

        :param division_type: type of a region
        :return: division category identifier
        """
        result = None
        if division_type in [
            ad.FEDERAL_STATE,
            ad.AREA_STATE,
            ad.FREE_STATE,
            ad.CITY_STATE,
        ]:
            result = 10
        elif division_type in [ad.GOVERNMENTAL_DISTRICT]:
            result = 20
        elif division_type in [ad.REGION]:
            result = 30
        elif division_type in [ad.RURAL_DISTRICT, ad.DISTRICT, ad.CITY_AND_DISTRICT]:
            result = 40
        elif division_type in [ad.COLLECTIVE_MUNICIPALITY]:
            result = 50
        elif division_type in [
            ad.CITY,
            ad.URBAN_DISTRICT,
            ad.MUNICIPALITY,
            ad.INITIAL_RECEPTION_CENTER,
        ]:
            result = 60
        return result

    def best_match(
        self, region_name: str | None, division_type: str | None
    ) -> dict[str, Any] | None:
        """
        Tries to find the correct region id (single search hit)

        :param region_name: name of a region (city name, county name, etc)
        :param division_type: administrative division type of region (choices: :mod:`~integreat_cms.cms.constants.administrative_division`)
        :return: JSON search results defined in the GVZ API
        """
        # First: let's try normal search. If there is only one result, then
        # everything is good.
        results = self.search(
            region_name, self.translate_division_category(division_type)
        )

        if len(results) == 1:
            logger.debug("GVZ API matching region for %r.", region_name)
            return results[0]
        # Second: drop all that are not literal matches:
        logger.debug("GVZ API found more than one region for %r.", region_name)
        results_literal = []
        for region in results:
            if "," in region["name"]:
                region["name"] = region["name"].split(",")[0]
            if region["name"] == region_name:
                results_literal.append(region)
        if len(results_literal) == 1:
            return results_literal[0]
        logger.debug("GVZ API did not find type match for %r", region_name)
        return None


class GvzRegion:
    """
    Represents a region in the GVZ, initial values will be retrieved
    from API on initialization.

    :param region_ags: official ID for a region, i.e. Gemeindeschlüssel, defaults to ``None``
    :param region_name: name of a region (city name, county name, etc), defaults to ``None``
    :param division_type: administrative division type of region (choices: :mod:`~integreat_cms.cms.constants.administrative_division`), defaults to ``None``
    """

    def __init__(
        self,
        region_ags: str | None = None,
        region_name: str | None = None,
        region_type: str | None = None,
    ) -> None:
        """
        Load initial values for region from GVZ API
        """
        if region_ags is None and region_name is None:
            return

        api = GvzApiWrapper()
        self.ags = region_ags
        if (
            region_name
            and not region_ags
            and (best_match := api.best_match(region_name, region_type))
        ):
            self.ags = best_match["ags"]

        self.name: str = region_name or ""
        self.longitude = None
        self.latitude = None
        self.child_coordinates = {}

        if self.ags and (details := api.get_details(self.ags)):
            self.id = details["id"]
            self.ags = details["ags"]
            self.name = self.name or details["name"]
            self.longitude = details["longitude"]
            self.latitude = details["latitude"]
            self.child_coordinates = api.get_child_coordinates(details["children"])

    def as_dict(self) -> dict[str, Any]:
        """
        Dictionary representation of region

        :return: name, longitude, latitude, list of children
        """
        return {
            "name": str(self),
            "longitude": self.longitude,
            "latitude": self.latitude,
            "children": self.child_coordinates,
        }

    def __str__(self) -> str:
        """
        String representation of region

        :return: name of region
        """
        return self.name

    def __repr__(self) -> str:
        """
        Canonical representation of GVZ region

        :return: Debugging representation of GVZ region
        """
        return f"<GvzRegion (name: {self.name}, ags: {self.ags}, longitude: {self.longitude}, latitude: {self.latitude})>"
