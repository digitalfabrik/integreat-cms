"""
Configuration of Nominatim API app
"""
import logging

from django.apps import apps, AppConfig
from django.conf import settings

from .nominatim_api_client import NominatimApiClient

logger = logging.getLogger(__name__)


class NominatimApiConfig(AppConfig):
    """
    Nominatim API config inheriting the Django AppConfig
    """

    name = "integreat_cms.nominatim_api"

    def ready(self):
        """
        Checking if API is available
        """
        # Only check availability if running a server
        if apps.get_app_config("cms").test_external_apis:
            # If Nominatim API is enabled, check availability
            if settings.NOMINATIM_API_ENABLED:
                NominatimApiClient().check_availability()
            else:
                logger.info("Nominatim API is disabled")
