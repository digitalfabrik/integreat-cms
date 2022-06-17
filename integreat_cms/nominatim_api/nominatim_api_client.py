import logging

from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

from integreat_cms import __version__

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
            )
        except GeopyError as e:
            logger.exception(e)
            logger.error("Nominatim API client could not be initialized")

    def search(self, query_str=None, exactly_one=True, **query_dict):
        r"""
        Search for a given query, either by string or by dict.
        ``query_str`` and ``query_dict`` are mutually exclusive.

        :raises RuntimeError: When the ``query_str`` and ``query_dict`` parameters are passed at the same time

        :param query_str: The query string
        :type query_str: str

        :param exactly_one: Whether only one result should be returned
        :type exactly_one: bool

        :param \**query_dict: The query as dictionary
        :type \**query_dict: dict

        :return: The location that matches the given criteria
        :rtype: geopy.location.Location
        """
        if query_str and query_dict:
            raise RuntimeError(
                "You can either specify query_str or pass additional keyword arguments, not both."
            )
        query = query_str or query_dict
        try:
            result = self.geolocator.geocode(
                query,
                exactly_one=exactly_one,
            )
            if result:
                logger.debug("Nominatim API search result: %r", result.raw)
            else:
                logger.debug("Nominatim API did not return a match")
            return result
        except GeopyError as e:
            logger.exception(e)
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
        except (GeopyError, AssertionError) as e:
            logger.exception(e)
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
