"""
Configuration of PushNotificationSender API app
"""
import json
import logging
import requests



from django.apps import apps, AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class PushNotificationSenderApiConfig(AppConfig):
    """
    PushNotificationSender API config inheriting the django AppConfig
    """

    name = "integreat_cms.push_notification_sender_api"
    api_available = False

    def ready(self):
        """
        Checking if API is available
        """
        # Only check availability if running a server
        if apps.get_app_config("cms").test_external_apis:
            if settings.FCM_ENABLED:
                try:
                    response = requests.get(
                        f"{settings.PUSH_NOTIFICATION_SENDER_API_URL}/api/", timeout=3
                    )
                    # Require the response to return a valid JSON, otherwise it's probably an error
                    assert json.loads(response.text)
                    logger.info(
                        "PushNotificationSender API is available at: %r",
                        settings.PUSH_NOTIFICATION_SENDER_API_URL,
                    )
                    self.api_available = True
                except (
                    json.decoder.JSONDecodeError,
                    requests.exceptions.RequestException,
                    requests.exceptions.Timeout,
                    AssertionError,
                ) as e:
                    logger.error(e)
                    logger.error(
                        "PushNotificationSender API is unavailable. You won't be able to "
                        "automatically import region coordinates and aliases."
                    )
            else:
                logger.info("PushNotificationSender API is disabled")
