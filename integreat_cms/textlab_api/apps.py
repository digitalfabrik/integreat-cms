from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.error import URLError

from django.apps import AppConfig, apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .textlab_api_client import TextlabClient

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


logger = logging.getLogger(__name__)


class TextlabApiConfig(AppConfig):
    """
    Textlab api config inheriting the django AppConfig
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.textlab_api"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("TextLab API")

    def ready(self) -> None:
        """
        Checking if api is available
        """
        # Only check availability if running a server
        if apps.get_app_config("core").test_external_apis:
            # If Textlab API is enabled, check availability
            if settings.TEXTLAB_API_ENABLED:
                try:
                    TextlabClient(
                        settings.TEXTLAB_API_USERNAME, settings.TEXTLAB_API_KEY
                    )
                    logger.info(
                        "Textlab API is available at: %r", settings.TEXTLAB_API_URL
                    )
                except (URLError, OSError) as e:
                    logger.info("Textlab API is unavailable: %r", e)
            else:
                logger.info("Textlab API is disabled")
