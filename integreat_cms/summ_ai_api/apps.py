"""
Configuration of SUMM.AI API app
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


class SummAiApiConfig(AppConfig):
    """
    SUMM.AI API config inheriting the django AppConfig
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.summ_ai_api"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("SUMM.AI API")

    def ready(self) -> None:
        """
        Inform about the SUMM.AI configuration
        """
        # Only check if running a server
        if apps.get_app_config("core").test_external_apis:
            if not settings.SUMM_AI_ENABLED:
                logger.info("SUMM.AI API is disabled")
            elif settings.SUMM_AI_TEST_MODE:
                logger.info(
                    "SUMM.AI API is enabled, but in test mode. No credits get charged, but only a dummy text is returned.",
                )
            elif settings.DEBUG:
                logger.info(
                    "SUMM.AI API is enabled, but in debug mode. Text is really translated and credits get charged, but user is 'testumgebung'",
                )
            else:
                logger.info("SUMM.AI API is enabled in production mode.")
