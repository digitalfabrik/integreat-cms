"""
Configuration of DeepL API app
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

from deepl import Translator
from deepl.exceptions import DeepLException
from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

logger = logging.getLogger(__name__)


class DeepLApiClientConfig(AppConfig):
    """
    DeepL API config inheriting the django AppConfig
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.deepl_api"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("DeepL API")
    #: The supported source languages
    supported_source_languages: list[str] = []
    #: The supported target languages
    supported_target_languages: list[str] = []

    def ready(self) -> None:
        """
        Checking if API is available
        """
        # Only check availability if running a server
        if "runserver" in sys.argv or "APACHE_PID_FILE" in os.environ:
            if settings.DEEPL_ENABLED:
                try:
                    deepl_translator = Translator(
                        auth_key=settings.DEEPL_AUTH_KEY,
                        server_url=settings.DEEPL_API_URL,
                    )

                    self.init_supported_source_languages(deepl_translator)
                    self.init_supported_target_languages(deepl_translator)

                    self.assert_usage_limit_not_reached(deepl_translator)
                except (DeepLException, AssertionError) as e:
                    logger.error(e)
                    logger.error(
                        "DeepL API is unavailable. You won't be able to "
                        "create and update machine translations."
                    )
            else:
                logger.info("DeepL API is disabled.")

    def init_supported_source_languages(self, translator: Translator) -> None:
        """
        Requests the supported sources languages from the translator and sets them

        :param translator: The deepl translator
        """
        self.supported_source_languages = [
            source_language.code.lower()
            for source_language in translator.get_source_languages()
        ]
        logger.debug(
            "Supported source languages by DeepL: %r",
            self.supported_source_languages,
        )
        assert self.supported_source_languages

    def init_supported_target_languages(self, translator: Translator) -> None:
        """
        Requests the supported target languages from the translator and sets them

        :param translator: The deepl translator
        """
        self.supported_target_languages = [
            target_languages.code.lower()
            for target_languages in translator.get_target_languages()
        ]
        logger.debug(
            "Supported target languages by DeepL: %r",
            self.supported_target_languages,
        )
        assert self.supported_target_languages

    @staticmethod
    def assert_usage_limit_not_reached(translator: Translator) -> None:
        """
        Requests the usage from the translator and asserts that no limit was reached

        :param translator: The deepl translator
        """
        usage = translator.get_usage()
        if usage.any_limit_reached:
            logger.warning("DeepL API translation limit reached")
        # pylint: disable=protected-access
        logger.info(
            "DeepL API is available at: %r (character usage: %s of %s)",
            translator._server_url,
            usage.character.count,
            usage.character.limit,
        )
