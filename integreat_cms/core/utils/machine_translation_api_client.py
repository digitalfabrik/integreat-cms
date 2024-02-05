"""
This module contains utilities for machine translation API clients
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from html import unescape
from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.html import strip_tags

if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from ...cms.models import (
        Event,
        EventTranslation,
        Page,
        PageTranslation,
        POI,
        POITranslation,
        Region,
    )

logger = logging.getLogger(__name__)


class MachineTranslationApiClient(ABC):
    """
    A base class for API clients interacting with machine translation APIs
    """

    #: The current request
    request: HttpRequest
    #: The current region
    region: Region
    #: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
    form_class: ModelFormMetaclass

    def __init__(self, request: HttpRequest, form_class: ModelFormMetaclass) -> None:
        """
        Constructor initializes the class variables

        :param region: The current region
        :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                           subclass of the current content type
        """
        self.request = request
        self.region = request.region
        self.form_class = form_class
        self.translatable_attributes = ["title", "content", "meta_description"]

    @abstractmethod
    def translate_queryset(
        self, queryset: QuerySet[Event | Page | POI], language_slug: str
    ) -> None:
        """
        Translate a given queryset into one specific language.
        Needs to be implemented by subclasses of MachineTranslationApiClient.

        :param queryset: The QuerySet of content objects to translate
        :param language_slug: The target language slug to translate into
        """

    def translate_object(self, obj: Event | Page | POI, language_slug: str) -> None:
        """
        This function translates one content object

        :param obj: The content object
        :param language_slug: The target language slug
        """
        return self.translate_queryset([obj], language_slug)

    def check_usage(
        self,
        region: Region,
        source_translation: EventTranslation | (PageTranslation | POITranslation),
    ) -> tuple[bool, int]:
        """
        This function checks if the attempted translation would exceed the region's word limit

        :param region: region for which to check usage
        :param source_translation: single content object
        :return: translation would exceed limit, region budget, attempted translation word count
        """
        # Gather content to be translated and calculate total word count
        attributes = [
            getattr(source_translation, attr, None)
            for attr in self.translatable_attributes
        ]
        content_to_translate = [
            unescape(strip_tags(attr)) for attr in attributes if attr
        ]

        content_to_translate_str = " ".join(content_to_translate)
        for char in "-;:,;!?\n":
            content_to_translate_str = content_to_translate_str.replace(char, " ")
        word_count = len(content_to_translate_str.split())

        # Check if translation would exceed MT usage limit
        region.refresh_from_db()
        # Allow up to MT_SOFT_MARGIN more words than the actual limit
        word_count_leeway = max(1, word_count - settings.MT_SOFT_MARGIN)
        translation_exceeds_limit = region.mt_budget_remaining < word_count_leeway

        return (translation_exceeds_limit, word_count)

    def __str__(self) -> str:
        """
        :return: A readable string representation of the machine translation API client
        """
        return type(self).__name__

    def __repr__(self) -> str:
        """
        :return: The canonical string representation of the machine translation API client
        """
        class_name = type(self).__name__
        return f"<{class_name} (request: {self.request!r}, region: {self.region!r}, form_class: {self.form_class})>"
