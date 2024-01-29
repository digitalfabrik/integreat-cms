"""
Configuration of Nominatim API app
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.apps import AppConfig, apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .nominatim_api_client import NominatimApiClient

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

logger = logging.getLogger(__name__)


class NominatimApiConfig(AppConfig):
    """
    Nominatim API config inheriting the Django AppConfig
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.nominatim_api"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("Nominatim API")

    def ready(self) -> None:
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
