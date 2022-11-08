import logging
import re

from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import override

from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from geopy.point import Point

from integreat_cms import __version__

from ..cms.constants import administrative_division as ad
from .utils import BoundingBox

logger = logging.getLogger(__name__)


class NominatimApiClient:
    """
    Client to interact with the Nominatim API.
    For documentation about the underlying library, see :doc:`GeoPy <geopy:index>`.
    """

    def __init__(self):
        """
        Initialize the Nominatim client

        :raises ~django.core.exceptions.ImproperlyConfigured: When the Nominatim API is disabled
        """
        if not settings.NOMINATIM_API_ENABLED:
            raise ImproperlyConfigured("Nominatim API is disabled")
        try:
            nominatim_url = urlparse(settings.NOMINATIM_API_URL)
            self.geolocator = Nominatim(
                domain=nominatim_url.netloc + nominatim_url.path,
                scheme=nominatim_url.scheme,
                user_agent=f"integreat-cms/{__version__} ({settings.HOSTNAME})",
                timeout=settings.DEFAULT_REQUEST_TIMEOUT,
            )
        except GeopyError as e:
            logger.exception(e)
            logger.error("Nominatim API client could not be initialized")

    def search(
        self, query_str=None, exactly_one=True, addressdetails=False, **query_dict
    ):
        r"""
        Search for a given query, either by string or by dict.
        ``query_str`` and ``query_dict`` are mutually exclusive.

        :raises RuntimeError: When the ``query_str`` and ``query_dict`` parameters are passed at the same time

        :param query_str: The query string
        :type query_str: str

        :param exactly_one: Whether only one result should be returned
        :type exactly_one: bool

        :param addressdetails: Whether address details should be returned
        :type addressdetails: bool

        :param \**query_dict: The query as dictionary
        :type \**query_dict: dict

        :return: The location that matches the given criteria
        :rtype: geopy.location.Location
        """
        if query_str and query_dict:
            raise RuntimeError(
                "You can either specify query_str or pass additional keyword arguments, not both."
            )
        if "street" in query_dict:
            # This expression matches a number optionally followed by a whitespace and one character
            street_number = r"\d+( ?[a-zA-Z])?"
            # This expression matches possible delimiters between multiple street numbers
            delimiter = r" ?[/,\-–] ?"
            # If multiple street numbers are given, only take the first one
            query_dict["street"] = re.sub(
                rf"({street_number})({delimiter}{street_number})+",
                r"\1",
                query_dict["street"],
            )
        query = query_str or query_dict
        try:
            result = self.geolocator.geocode(
                query,
                exactly_one=exactly_one,
                addressdetails=addressdetails,
            )
            if result:
                logger.debug("Nominatim API search result: %r", result.raw)
            else:
                logger.debug("Nominatim API did not return a match")
            return result
        except GeopyError as e:
            logger.error(e)
            logger.error("Nominatim API call failed")
            return None

    def check_availability(self):
        """
        Check if Nominatim API is available
        """
        try:
            assert self.search(query_str="Deutschland")
            logger.info(
                "Nominatim API is available at: %r",
                settings.NOMINATIM_API_URL,
            )
        except AssertionError:
            logger.error(
                "Nominatim API unavailable. You won't be able to "
                "automatically import location coordinates."
            )

    def get_coordinates(self, street, postalcode, city):
        """
        Get coordinates for given address

        :param street: The requested street
        :type street: str

        :param postalcode: The requested postal code
        :type postalcode: str

        :param city: The requested city
        :type city: str

        :return: The coordinates of the requested address
        :rtype: tuple ( float, float )
        """
        result = self.search(street=street, postalcode=postalcode, city=city)
        if result:
            return result.latitude, result.longitude
        return None, None

    def get_bounding_box(self, administrative_division, name, aliases=None):
        """
        Get the bounding box for a given region

        :param administrative_division: The administrative division of the requested region
        :type administrative_division: str

        :param name: The name of the requested region
        :type name: str

        :param aliases: A dictionary of region aliases
        :type aliases: dict

        :return: The bounding box
        :rtype: ~integreat_cms.nominatim_api.utils.BoundingBox
        """
        if administrative_division in [
            ad.CITY,
            ad.MUNICIPALITY,
            ad.CITY_STATE,
            ad.URBAN_DISTRICT,
            ad.COLLECTIVE_MUNICIPALITY,
        ]:
            return self.get_city_bounding_box(name)
        if administrative_division == ad.CITY_AND_DISTRICT:
            return self.get_city_and_district_bounding_box(name)
        if administrative_division in [ad.DISTRICT, ad.RURAL_DISTRICT]:
            return self.get_district_bounding_box(administrative_division, name)
        if administrative_division == ad.REGION:
            return self.get_region_bounding_box(name, aliases)
        return None

    def get_city_bounding_box(self, name):
        """
        Get the bounding box for a given city

        :param name: The name of the requested region
        :type name: str

        :return: The bounding box
        :rtype: ~integreat_cms.nominatim_api.utils.BoundingBox
        """
        # For cities and municipalities, we can just use the "city" parameter
        return BoundingBox.from_result(self.search(city=name))

    def get_city_and_district_bounding_box(self, name):
        """
        Get the bounding box for a given city and district

        :param name: The name of the requested region
        :type name: str

        :return: The bounding box
        :rtype: ~integreat_cms.nominatim_api.utils.BoundingBox
        """
        # Get bounding box of city
        city_box = BoundingBox.from_result(self.search(city=name))
        # Get bounding box of district
        district_box = BoundingBox.from_result(
            self.search(query_str=f"Landkreis {name}")
        )
        # Merge both results
        return BoundingBox.merge(city_box, district_box)

    def get_district_bounding_box(self, administrative_division, name):
        """
        Get the bounding box for a given district

        :param administrative_division: The administrative division of the requested region
        :type administrative_division: str

        :param name: The name of the requested region
        :type name: str

        :return: The bounding box
        :rtype: ~integreat_cms.nominatim_api.utils.BoundingBox
        """
        # Get translated name of the administrative division
        with override(settings.LANGUAGE_CODE):
            adm_div = dict(ad.CHOICES)[administrative_division]
        # For districts, we have to use string queries
        return BoundingBox.from_result(self.search(query_str=f"{adm_div} {name}"))

    def get_region_bounding_box(self, name, aliases=None):
        """
        Get the bounding box for a given region and all its aliases

        :param name: The name of the requested region
        :type name: str

        :param aliases: A dictionary of region aliases
        :type aliases: dict

        :return: The bounding box
        :rtype: ~integreat_cms.nominatim_api.utils.BoundingBox
        """
        if not aliases:
            aliases = {}
        # Get bounding box of city
        bounding_boxes = [BoundingBox.from_result(self.search(city=name))]
        # Get bounding boxes of all aliases
        for alias in aliases.keys():
            bounding_boxes.append(BoundingBox.from_result(self.search(city=alias)))
        return BoundingBox.merge(*bounding_boxes)

    def get_address(self, latitude, longitude):
        """
        Get coordinates for given address

        :param latitude: The requested latitude
        :type latitude: str

        :param longitude: The requested longitude
        :type longitude: str

        :return: The address at these coordinates
        :rtype: dict
        """
        coordinates = Point(latitude, longitude)
        try:
            result = self.geolocator.reverse(coordinates)
            if result:
                logger.debug("Nominatim API reverse search result: %r", result.raw)
            else:
                logger.debug(
                    "Nominatim API did not return an address at coordinates %r",
                    coordinates,
                )
            return result
        except GeopyError as e:
            logger.error(e)
            logger.error("Nominatim API call failed")
            return None
