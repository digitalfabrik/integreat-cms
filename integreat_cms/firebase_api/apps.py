"""
Configuration of the Firebase API app
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.apps import AppConfig, apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

logger = logging.getLogger(__name__)


class FirebaseApiConfig(AppConfig):
    """
    Firebase API config inheriting the django AppConfig
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.firebase_api"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("Firebase API")

    def ready(self) -> None:
        """
        Checking if API is available
        """
        # Only check if running a server
        if apps.get_app_config("core").test_external_apis:
            if not settings.FCM_ENABLED:
                logger.info("Firebase Cloud Messaging is disabled")
            elif settings.DEBUG:
                logger.info(
                    "Firebase Cloud Messaging is enabled, but in debug mode. "
                    "Push notifications are really sent, but only to the test region.",
                )
            else:
                logger.info("Firebase Cloud Messaging is enabled in production mode.")
