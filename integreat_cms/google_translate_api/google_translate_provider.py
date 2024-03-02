from __future__ import annotations

import logging

from django.apps import apps
from django.conf import settings
from django.utils.functional import classproperty

from ..core.utils.machine_translation_provider import MachineTranslationProvider
from .google_translate_api_client import GoogleTranslateApiClient

logger = logging.getLogger(__name__)


class GoogleTranslateProvider(MachineTranslationProvider):
    """
    The provider for Google machine translations
    """

    #: The readable name for this provider
    name = "Google Translate"
    #: The API client class for this provider
    api_client = GoogleTranslateApiClient
    #: Whether the provider is globally enabled
    enabled = settings.GOOGLE_TRANSLATE_ENABLED

    @classmethod
    @classproperty
    def supported_source_languages(cls) -> list[str]:
        """
        The supported source languages

        :return: The list of supported source languages
        """
        return apps.get_app_config("google_translate_api").supported_source_languages

    @classmethod
    @classproperty
    def supported_target_languages(cls) -> list[str]:
        """
        The supported target languages

        :return: The list of supported target languages
        """
        return apps.get_app_config("google_translate_api").supported_target_languages
