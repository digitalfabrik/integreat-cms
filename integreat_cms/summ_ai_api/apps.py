"""
Configuration of SUMM.AI API app
"""
import logging

from django.conf import settings
from django.apps import apps, AppConfig

logger = logging.getLogger(__name__)


class SummAiApiConfig(AppConfig):
    """
    SUMM.AI API config inheriting the django AppConfig
    """

    name = "integreat_cms.summ_ai_api"

    def ready(self):
        """
        Inform about the SUMM.AI configuration
        """
        # Only check if running a server
        if apps.get_app_config("cms").test_external_apis:
            if not settings.SUMM_AI_ENABLED:
                logger.info("SUMM.AI API is disabled")
            elif settings.SUMM_AI_TEST_MODE:
                logger.info(
                    "SUMM.AI API is enabled, but in test mode. No credits get charged, but only a dummy text is returned."
                )
            elif settings.DEBUG:
                logger.info(
                    "SUMM.AI API is enabled, but in debug mode. Text is really translated and credits get charged, but user is 'testumgebung'"
                )
            else:
                logger.info("SUMM.AI API is enabled in production mode.")
