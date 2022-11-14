"""
Configuration of the Firebase API app
"""
import logging


from django.apps import apps, AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class FirebaseApiConfig(AppConfig):
    """
    Firebase API config inheriting the django AppConfig
    """

    name = "integreat_cms.firebase_api"

    def ready(self):
        """
        Checking if API is available
        """
        # Only check if running a server
        if apps.get_app_config("cms").test_external_apis:
            if not settings.FCM_ENABLED:
                logger.info("Firebase Cloud Messaging is disabled")
            elif settings.DEBUG:
                logger.info(
                    "Firebase Cloud Messaging is enabled, but in debug mode. "
                    "Push notifications are really sent, but only to the test region."
                )
            else:
                logger.info("Firebase Cloud Messaging is enabled in production mode.")
