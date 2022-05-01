"""
Configuration of DeepL API app
"""
import os
import sys
import logging

from deepl.exceptions import DeepLException

from django.apps import AppConfig
from django.conf import settings

from .utils import DeepLApi

logger = logging.getLogger(__name__)


class DeepLApiConfig(AppConfig):
    """
    DeepL API config inheriting the django AppConfig
    """

    name = "integreat_cms.deepl_api"
    supported_source_languages = []
    supported_target_languages = []

    def ready(self):
        """
        Checking if API is available
        """
        # Only check availability if running a server
        if "runserver" in sys.argv or "APACHE_PID_FILE" in os.environ:
            if settings.DEEPL_ENABLED:
                try:
                    deepl = DeepLApi()
                    self.supported_source_languages = [
                        source_language.code.lower()
                        for source_language in deepl.translator.get_source_languages()
                    ]
                    logger.debug(
                        "Supported source languages by DeepL: %r",
                        self.supported_source_languages,
                    )
                    assert self.supported_source_languages
                    self.supported_target_languages = [
                        target_languages.code.lower()[:2]
                        for target_languages in deepl.translator.get_target_languages()
                    ]
                    logger.debug(
                        "Supported target languages by DeepL: %r",
                        self.supported_target_languages,
                    )
                    assert self.supported_target_languages
                    # pylint: disable=protected-access
                    logger.info(
                        "DeepL API is available at: %r", deepl.translator._server_url
                    )
                except (DeepLException, AssertionError) as e:
                    logger.exception(e)
                    logger.error(
                        "DeepL API is unavailable. You won't be able to "
                        "automatically translate events and locations."
                    )
            else:
                logger.info("DeepL API is disabled.")
