"""
Configuration of GVZ API app
"""
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

    name = 'gvz_api'
    api_available = False

    def ready(self):
        """
        Checking if API is available
        """
        if settings.GVZ_API_ENABLED:
            try:
                response = requests.get(
                    "{}/search/expect_empty_json".format(settings.GVZ_API_URL))
                json.loads(response.text)
            except json.decoder.JSONDecodeError:
                self.api_available = False
            except requests.exceptions.RequestException:
                self.api_available = False
            else:
                self.api_available = True
        else:
            self.api_available = False
        if not self.api_available:
            logger.info("GVZ API is not available. You won't be able to "
                        "automatically import coordinates and region aliases.")
        else:
            self.api_available = True
            logger.info("GVZ API is available.")
