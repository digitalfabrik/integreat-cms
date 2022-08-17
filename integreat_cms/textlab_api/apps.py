import logging
from urllib.error import URLError

from django.apps import apps, AppConfig
from django.conf import settings

from .textlab_api_client import TextlabClient

logger = logging.getLogger(__name__)


class TextlabApiConfig(AppConfig):
    """
    Textlab api config inheriting the django AppConfig
    """

    name = "integreat_cms.textlab_api"

    def ready(self):
        """
        Checking if api is available
        """
        # Only check availability if running a server
        if apps.get_app_config("cms").test_external_apis:
            # If Textlab API is enabled, check availability
            if settings.TEXTLAB_API_ENABLED:
                try:
                    TextlabClient(
                        settings.TEXTLAB_API_USERNAME, settings.TEXTLAB_API_KEY
                    )
                    logger.info(
                        "Textlab API is available at: %r", settings.TEXTLAB_API_URL
                    )
                except URLError:
                    logger.info("Textlab API is unavailable")
            else:
                logger.info("Textlab API is disabled")
