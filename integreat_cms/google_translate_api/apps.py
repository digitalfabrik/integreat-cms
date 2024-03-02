"""
Configuration of Google Translate API app
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from google.cloud import translate_v2, translate_v3  # type: ignore[attr-defined]
from google.oauth2 import service_account

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise
    from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


class GoogleTranslateApiClientConfig(AppConfig):
    """
    Google Translate API config inheriting the django AppConfig
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.google_translate_api"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("Google Translate API")
    #: The supported source languages
    supported_source_languages: list[str] = []
    #: The supported target languages
    supported_target_languages: list[str] = []

    def ready_v2(self, credentials: Credentials) -> None:
        """
        Preparing Google Translate with basic version
        """
        logger.info(translate_v2)
        google_translator_v2 = translate_v2.Client(credentials=credentials)

        # Version 2 (Basic) does not distinguish source and target language
        supported_languages = google_translator_v2.get_languages()
        self.supported_source_languages = []
        self.supported_target_languages = []

        for language in supported_languages:
            self.supported_source_languages += [language["language"]]
            self.supported_target_languages += [language["language"]]

    def ready_v3(self, credentials: Credentials) -> None:
        """
        Preparing Google Translate with advanced version
        """
        logger.info(translate_v3)
        google_translator_v3 = translate_v3.TranslationServiceClient(
            credentials=credentials
        )

        parent = settings.GOOGLE_PARENT_PARAM

        supported_languages = google_translator_v3.get_supported_languages(
            parent=parent
        ).languages

        self.supported_source_languages = []
        self.supported_target_languages = []

        for language in supported_languages:
            if language.support_source:
                self.supported_source_languages += [language.language_code]
            if language.support_target:
                self.supported_target_languages += [language.language_code]

    def ready(self) -> None:
        """
        Checking if API is available
        """
        # Only check availability if running a server
        if "runserver" in sys.argv or "APACHE_PID_FILE" in os.environ:
            if settings.GOOGLE_TRANSLATE_ENABLED:
                try:
                    credentials = service_account.Credentials.from_service_account_file(
                        settings.GOOGLE_APPLICATION_CREDENTIALS
                    )
                    if settings.GOOGLE_TRANSLATE_VERSION == "Advanced":
                        self.ready_v3(credentials)
                    else:
                        self.ready_v2(credentials)

                    assert (
                        self.supported_source_languages
                    ), "No supported source languages by Google Translate"
                    logger.debug(
                        "Supported source languages by Google Translate: %r",
                        self.supported_source_languages,
                    )

                    assert (
                        self.supported_source_languages
                    ), "No supported target languages by Google Translate"
                    logger.debug(
                        "Supported target languages by Google Translate: %r",
                        self.supported_target_languages,
                    )

                    logger.info("Google Translate API is enabled.")
                except Exception as e:  # pylint: disable=broad-except
                    logger.error(e)
                    logger.error("Google translate is not available.")
            else:
                logger.info("Google Translate API is disabled.")
