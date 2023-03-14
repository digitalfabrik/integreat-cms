"""
Configuration of Nominatim API app
"""
import logging

from django.apps import AppConfig, apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .nominatim_api_client import NominatimApiClient

logger = logging.getLogger(__name__)


class NominatimApiConfig(AppConfig):
    """
    Nominatim API config inheriting the Django AppConfig
    """

    #: Full Python path to the application
    name = "integreat_cms.nominatim_api"
    #: Human-readable name for the application
    verbose_name = _("Nominatim API")

    def ready(self):
        """
        Checking if API is available
        """
        # Only check availability if running a server
        if apps.get_app_config("core").test_external_apis:
            # If Nominatim API is enabled, check availability
            if settings.NOMINATIM_API_ENABLED:
                NominatimApiClient().check_availability()
            else:
                logger.info("Nominatim API is disabled")
