"""
This module contains the available machine translation providers
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...deepl_api.deepl_provider import DeepLProvider
from ...google_translate_api.google_translate_provider import GoogleTranslateProvider
from ...summ_ai_api.summ_ai_provider import SummAiProvider

if TYPE_CHECKING:
    from typing import Final, Type

    from ...core.utils.machine_translation_provider import MachineTranslationProvider


CHOICES: Final[list[Type[MachineTranslationProvider]]] = [
    DeepLProvider,
    GoogleTranslateProvider,
    SummAiProvider,
]
