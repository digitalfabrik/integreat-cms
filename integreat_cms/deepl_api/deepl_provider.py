from __future__ import annotations

import logging

from django.apps import apps
from django.conf import settings
from django.utils.functional import classproperty

from ..core.utils.machine_translation_provider import MachineTranslationProvider
from .deepl_api_client import DeepLApiClient

logger = logging.getLogger(__name__)


class DeepLProvider(MachineTranslationProvider):
    """
    The provider for DeepL machine translations
    """

    #: The readable name for this provider
    name = "DeepL"
    #: The API client class for this provider
    api_client = DeepLApiClient
    #: Whether the provider is globally enabled
    enabled = settings.DEEPL_ENABLED

    @classmethod
    @classproperty
    def supported_source_languages(cls) -> list[str]:
        """
        The supported source languages

        :return: The list of supported source languages
        """
        return apps.get_app_config("deepl_api").supported_source_languages

    @classmethod
    @classproperty
    def supported_target_languages(cls) -> list[str]:
        """
        The supported target languages

        :return: The list of supported target languages
        """
        return apps.get_app_config("deepl_api").supported_target_languages
