"""
Helper classes for Gemeindeverzeichnis API
"""
import logging
import json
import requests
from django.conf import settings
from cms.constants import administrative_division

logger = logging.getLogger(__name__)


class GvzApiWrapper:
    """
    Class that wraps around the GVZ (Gemeindeverzeichnis) API
    """

    api_url = settings.GVZ_API_URL
    """
    The URL to the external GVZ API
    """

    def search(self, region_name):
        """
        Search for a region and return candidates

        :param region_name: name of a region (city name, county name, etc)
        :type region_name: str

        :return: JSON search results defined in the GVZ API
        :rtype: str
        """

        logger.debug("Searching for %r", region_name)
        response = requests.get(f"{self.api_url}/search/{region_name}")
        regions = json.loads(response.text)
        return regions

    def get_details(self, region_key):
        """
        Get details for a region key (i.e. Gemeindeschlüssel)

        :param region_key: official ID for a region, i.e. Gemeindeschlüssel
        :type region_key: str

        :return: dictionary containing longitude, latitude, type, key, name
        :rtype: dict
        """
        logger.debug("GVZ API: Details for %r", region_key)
        response = requests.get(f"{self.api_url}/details/{region_key}")
        region = json.loads(response.text)
        if len(region) != 1:
            return None
        region = region[0]
        if "," in region["name"]:
            region["name"] = region["name"].split(",")[0]
        return {
            "key": region["key"],
            "name": region["name"],
            "longitude": region["longitude"],
            "latitude": region["latitude"],
            "type": region["type"],
        }

    def get_children(self, region_key):
        """
        Get keys of children of a region

        :param region_key: official ID for a region, i.e. Gemeindeschlüssel
        :type region_key: str

        :return: list of children dictionaries
        :rtype: list
        """
        response = requests.get(f"{self.api_url}/searchcounty/{region_key}")
        content = json.loads(response.text)
        if content:
            return content[0]["children"]
        return []

    @staticmethod
    def translate_type(region_type):
        """
        Map Integreat CMS region types to Gemeindeverzeichnis region types.

        :param region_type: type of a region
        :type region_type: str

        :return: administrative division of the region (choices: :mod:`cms.constants.administrative_division`)
        :rtype: str
        """
        if region_type in ("Stadt", "Kreisfreie Stadt"):
            return administrative_division.CITY
        if region_type in ("Landkreis", "Kreis"):
            return administrative_division.RURAL_DISTRICT
        return None

    @classmethod
    def filter_region_types(cls, region_details):
        """
        Special filters for certain region types. For example, Kreisfreie
        Städte exist multiple times on different levels. We want the lower
        level that contain the coordinates.

        :param region_details: dictionary with region details
        :type region_details: dict

        :return: indicates if a region is not interesting
        :rtype: bool
        """
        if cls.translate_type(region_details["type"]) == administrative_division.CITY:
            if len(region_details["key"]) <= 5:
                return False
        return True

    def best_match(self, region_name, region_type=None):
        """
        Tries to find the correct region key (single search hit)

        :param region_name: name of a region (city name, county name, etc)
        :type region_name: str

        :param region_type: administrative division type of region (choices: :mod:`cms.constants.administrative_division`), defaults to ``None``
        :type region_type: str

        :return: JSON search results defined in the GVZ API
        :rtype: str
        """
        # First: let's try normal search. If there is only one result, then
        # everything is good.
        results = self.search(region_name)
        if len(results) == 1:
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
        logger.debug("GVZ API did not find literal match for %r.", region_name)
        # Third: match type
        if region_type is None:
            return None
        results_type = []
        for region in results_literal:
            region_details = self.get_details(region["key"])
            if region_details is None:
                continue
            if self.filter_region_types(region_details):
                if self.translate_type(region_details["type"]) == region_type:
                    results_type.append(region)
        if len(results_type) == 1:
            return results_type[0]
        print(results_type)
        logger.debug("GVZ API did not find type match for %r", region_name)
        return None


class GvzRegion:
    """
    Represents a region in the GVZ, initial values will be retrieved
    from API on initialization.

    :param region_key: official ID for a region, i.e. Gemeindeschlüssel, defaults to ``None``
    :type region_key: str

    :param region_name: name of a region (city name, county name, etc), defaults to ``None``
    :type region_name: str

    :param region_type: administrative division type of region (choices: :mod:`cms.constants.administrative_division`), defaults to ``None``
    :type region_type: str
    """

    def __init__(self, region_key=None, region_name=None, region_type=None):
        """
        Load initial values for region from GVZ API
        """
        if region_key is None and region_name is None:
            return

        api = GvzApiWrapper()
        self.key = region_key
        if region_name is not None and region_key == "":
            best_match = api.best_match(region_name, region_type)
            if best_match is not None:
                self.key = best_match["key"]

        self.name = None
        self.longitude = None
        self.latitude = None
        self.children = []

        if self.key is None or self.key == "":
            return

        details = api.get_details(self.key)
        if details is None:
            return
        self.name = details["name"]
        self.longitude = details["longitude"]
        self.latitude = details["latitude"]

        children = api.get_children(self.key)
        for child in children:
            self.children.append(GvzRegion(region_key=child["key"]))

    def as_dict(self):
        """
        Dictionary representation of region

        :return: name, longitude, latitude, list of children
        :rtype: dict
        """
        return {
            "name": str(self),
            "longitude": self.longitude,
            "latitude": self.latitude,
            "children": [child.as_dict() for child in self.children],
        }

    def __str__(self):
        """
        String representation of region

        :return: name of region
        :rtype: str
        """
        return self.name

    @property
    def aliases(self):
        """
        Returns JSON of region aliases compliant to Integreat API v3 definition

        :return: aliases of region according to Integreat APIv3 definition
        :rtype: str
        """
        aliases = {}
        if self.children is None:
            return ""
        for child in self.children:
            aliases[child.name] = {
                "longitude": child.longitude,
                "latitude": child.latitude,
            }
        return json.dumps(aliases)
