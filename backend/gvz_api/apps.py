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

    def ready(self):
        """
        Checking if API is available
        """

        r = requests.get("{}/search/expect_empty_json".format(settings.GVZ_API_URL))
        if not json.loads(r.text):
            logger.info("GVZ API is available.")
        else:
            logger.warn("GVZ API is not available. You won't be able to automatically import coordinates and city aliases.")
