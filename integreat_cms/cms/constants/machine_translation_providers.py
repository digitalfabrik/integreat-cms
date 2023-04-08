"""
This module contains the available machine translation providers
"""
from ...deepl_api.deepl_provider import DeepLProvider
from ...summ_ai_api.summ_ai_provider import SummAiProvider

CHOICES = [DeepLProvider, SummAiProvider]
