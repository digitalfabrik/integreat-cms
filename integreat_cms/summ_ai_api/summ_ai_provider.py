from __future__ import annotations

import logging

from django.conf import settings

from ..core.utils.machine_translation_provider import MachineTranslationProvider
from .summ_ai_api_client import SummAiApiClient

logger = logging.getLogger(__name__)


class SummAiProvider(MachineTranslationProvider):
    """
    The provider for SUMM.AI machine translations
    """

    #: The readable name for this provider
    name = "SUMM.AI"
    #: The API client class for this provider
    api_client = SummAiApiClient
    #: Whether to require the staff permission for bulk actions
    bulk_only_for_staff = True
    #: Whether the provider is globally enabled
    enabled = settings.SUMM_AI_ENABLED
    #: The name of the region attribute which denotes whether the provider is enabled in a region
    region_enabled_attr = "summ_ai_enabled"
    #: The supported source languages
    supported_source_languages = [settings.SUMM_AI_GERMAN_LANGUAGE_SLUG]
    #: The supported target languages
    supported_target_languages = [settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG]
