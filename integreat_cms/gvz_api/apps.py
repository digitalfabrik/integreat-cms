"""
Configuration of GVZ API app
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import requests
from django.apps import AppConfig, apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

logger = logging.getLogger(__name__)


class GvzApiConfig(AppConfig):
    """
    GVZ API config inheriting the django AppConfig
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.gvz_api"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("GVZ API")
    #: Whether the API is available
    api_available: bool = False

    def ready(self) -> None:
        """
        Checking if API is available
        """
        # Only check availability if running a server
        if apps.get_app_config("core").test_external_apis:
            if settings.GVZ_API_ENABLED:
                try:
                    response = requests.get(f"{settings.GVZ_API_URL}/api/", timeout=3)
                    # Require the response to return a valid JSON, otherwise it's probably an error
                    assert json.loads(response.text)
                    logger.info("GVZ API is available at: %r", settings.GVZ_API_URL)
                    self.api_available = True
                except (
                    json.decoder.JSONDecodeError,
                    requests.exceptions.RequestException,
                    requests.exceptions.Timeout,
                    AssertionError,
                ) as e:
                    logger.error(e)
                    logger.error(
                        "GVZ API is unavailable. You won't be able to "
                        "automatically import region coordinates and aliases."
                    )
            else:
                logger.info("GVZ API is disabled")
