"""
Configuration of GVZ API app
"""
import os
import sys
import logging
import json
import requests
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class GvzApiConfig(AppConfig):
    """
    GVZ API config inheriting the django AppConfig
    """

    name = "integreat_cms.gvz_api"
    api_available = False

    def ready(self):
        """
        Checking if API is available
        """
        # Only check availability if running a server
        if "runserver" in sys.argv or "APACHE_PID_FILE" in os.environ:
            if settings.GVZ_API_ENABLED:
                try:
                    response = requests.get(f"{settings.GVZ_API_URL}/api/", timeout=3)
                    # Require the response to return a valid JSON, otherwise it's probably an error
                    assert json.loads(response.text)
                except (
                    json.decoder.JSONDecodeError,
                    requests.exceptions.RequestException,
                    requests.exceptions.Timeout,
                    AssertionError,
                ):
                    logger.info(
                        "GVZ API is not available. You won't be able to "
                        "automatically import coordinates and region aliases."
                    )
                else:
                    self.api_available = True
                    logger.debug("GVZ API is available.")
            else:
                logger.debug("GVZ API is not enabled.")
