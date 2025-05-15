"""
This module contains utilities for machine translation API clients
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.utils.translation import ngettext, ngettext_lazy

from ...cms.constants.machine_translatable_attributes import TRANSLATABLE_ATTRIBUTES
from ...cms.utils.stringify_list import iter_to_string
from ...textlab_api.utils import check_hix_score
from .word_count import word_count

if TYPE_CHECKING:
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from ...cms.models import (
        Event,
        Language,
        Page,
        POI,
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
    #: Successful translations
    successful_translations: list[Event] | list[Page] | list[POI] = []
    #: Translations with an attached API failure
    failed_translations: list[str] = []
    #: Content objects untranslatable due to missing source translations
    failed_because_no_source_translation: list[str] = []
    #: Content objects untranslatable due to too-low hix score
    failed_because_insufficient_hix_score: list[str] = []
    #: Content objects untranslatable due to insufficient translation budget
    failed_because_exceeds_limit: list[str] = []

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
        self.translatable_attributes = TRANSLATABLE_ATTRIBUTES

    def reset(self) -> None:
        """
        A single instance of a MachineTranslationApiClient may
        be used multiple times in succession, requiring a reset
        of the stored results and failures.

        Forgetting to call this function will not result in additional
        machine translation budget use, but will produce nonsense messages
        shown to the user.
        """
        self.successful_translations = []
        self.failed_translations = []
        self.failed_because_no_source_translation = []
        self.failed_because_insufficient_hix_score = []
        self.failed_because_exceeds_limit = []

    @abstractmethod
    def invoke_translation_api(self) -> None:
        """
        Translate all content objects stored in self.queryset.
        Needs to be implemented by subclasses of MachineTranslationApiClient.
        """

    @staticmethod
    @abstractmethod
    def get_target_language_key(target_language: Language) -> str:
        """
        This function decides the correct target language key
        Needs to be implemented by subclasses of MachineTranslationApiClient.

        :param target_language: the target language
        :return: target_language_key which is 2 characters long for all languages except English and Portuguese where the BCP tag is transmitted
        """

    def translate_object(self, obj: Event | Page | POI, language_slug: str) -> None:
        """
        This function translates one content object

        :param obj: The content object
        :param language_slug: The target language slug
        """
        return self.translate_queryset([obj], language_slug)

    @transaction.atomic
    def translate_queryset(
        self,
        queryset: list[Event] | (list[Page] | list[POI]),
        language_slug: str,
    ) -> None:
        """
        This function translates a content queryset via DeepL

        :param queryset: The content QuerySet
        :param language_slug: The target language slug
        """
        if not queryset:
            return

        self.reset()

        # Re-select the region from db to prevent simultaneous
        # requests exceeding the DeepL usage limit
        region = (
            apps.get_model("cms", "Region")
            .objects.select_for_update()
            .get(id=self.request.region.id)
        )

        # Store parameters used by all content objects
        self.source_language = region.get_source_language(language_slug)
        self.target_language = region.get_language_or_404(language_slug)
        self.target_language_key = self.get_target_language_key(self.target_language)
        self.queryset = queryset
        self.region = region

        # Store content object info for later use in messages shown to user
        meta = type(self.queryset[0])._meta
        self.model_name = meta.verbose_name.title()
        self.model_name_plural = meta.verbose_name_plural

        # Filter out content objects which can not be translated
        self.prepare_content_objects()
        self.filter_no_source_translation()
        self.filter_insufficient_hix_score()
        self.filter_exceeds_limit()

        # Provider-API-spcific implementation
        self.invoke_translation_api()

        # Update remaining budget of the region
        region.mt_budget_used += sum(
            content_object.word_count for content_object in self.successful_translations
        )
        region.save()

        # Show success/error messages to the user
        self.alert_successful_translations()
        self.alert_failed_translations()
        self.alert_no_source_translation()
        self.alert_insufficient_hix_score()
        self.alert_exceeds_limit()

    def filter_no_source_translation(self) -> None:
        """
        This method removes content objects from the main queryset
        if they do not have the required source translation.

        The removed elements are stored in order to show users
        batched error messages after all objects have been handled.

        :param source_language: The source language slug
        """
        filtered_queryset = []

        for content_object in self.queryset:
            if content_object.source_translation:
                filtered_queryset.append(content_object)
            else:
                self.failed_because_no_source_translation.append(
                    content_object.best_translation.title
                )

        self.queryset[:] = filtered_queryset

    def filter_insufficient_hix_score(self) -> None:
        """
        This method removes content objects from the main queryset
        if they do not have the required HIX score.

        The removed elements are stored in order to show users
        batched error messages after all objects have been handled.

        :param source_language: The source language slug
        """
        filtered_queryset = []

        for content_object in self.queryset:
            if check_hix_score(
                self.request,
                content_object.source_translation,
                show_message=False,
            ):
                filtered_queryset.append(content_object)
            else:
                self.failed_because_insufficient_hix_score.append(
                    content_object.source_translation.title
                )

        self.queryset[:] = filtered_queryset

    def filter_exceeds_limit(self) -> None:
        """
        This method removes content objects from the main queryset
        if translating them would exceed the translation budget.

        The removed elements are stored in order to show users
        batched error messages after all objects have been handled.

        :param source_language: The source language slug
        """
        remaining_budget = self.region.mt_budget_remaining
        filtered_queryset = []

        for content_object in self.queryset:
            if (
                max(1, content_object.word_count - settings.MT_SOFT_MARGIN)
                < remaining_budget
            ):
                filtered_queryset.append(content_object)
                remaining_budget -= content_object.word_count
            else:
                self.failed_because_exceeds_limit.append(
                    content_object.source_translation.title
                )

        self.queryset[:] = filtered_queryset

    def prepare_content_objects(self) -> None:
        """
        Prepare the content objects to be translated by annotating
        them with information which otherwise would need to be
        recalculated multiple times.
        """
        for content_object in self.queryset:
            content_object.source_translation = content_object.get_translation(
                self.source_language.slug,
            )
            content_object.existing_target_translation = content_object.get_translation(
                self.target_language.slug,
            )
            content_object.translatable_attributes = [
                (attr, getattr(content_object.source_translation, attr))
                for attr in self.translatable_attributes
                if hasattr(content_object.source_translation, attr)
                and getattr(content_object.source_translation, attr)
                and not (content_object.do_not_translate_title and attr == "title")
            ]
            content_object.word_count = word_count(
                content_object.translatable_attributes,
            )

    def mark_successful(self, content_object: Event | Page | POI) -> None:
        """
        Mark a content object as having been translated successfully
        """
        logger.debug(
            "Successfully translated for: %r",
            content_object.existing_target_translation,
        )
        self.successful_translations.append(content_object)

    def mark_unsuccessful(
        self, content_object: Event | Page | POI, errors: bool
    ) -> None:
        """
        Mark a translation as unuccessfull (usually due to API errors)
        """
        logger.error(
            "Automatic translation for %r could not be created because of %r",
            content_object,
            errors,
        )
        self.failed_translations.append(content_object.source_translation.title)

    def save_translation(
        self, content_object: Event | Page | POI, translation_data: dict
    ) -> None:
        """
        Create a translation form based on the extracted content object data,
        save it, and validate the translation.
        """
        content_translation_form = self.form_class(
            data=translation_data,
            instance=content_object.existing_target_translation,
            additional_instance_attributes={
                "creator": self.request.user,
                "language": self.target_language,
                content_object.source_translation.foreign_field(): content_object,
            },
        )

        # Validate content translation
        if content_translation_form.is_valid():
            content_translation_form.save()
            # Revert "currently in translation" value of all versions
            if content_object.existing_target_translation:
                if settings.REDIS_CACHE:
                    content_object.existing_target_translation.all_versions.invalidated_update(
                        currently_in_translation=False,
                    )
                else:
                    content_object.existing_target_translation.all_versions.update(
                        currently_in_translation=False,
                    )

            self.mark_successful(content_object)
        else:
            self.mark_unsuccessful(content_object, content_translation_form.errors)

    def alert_successful_translations(self) -> None:
        """
        Add messages informing the user about successful translations
        """
        if not self.successful_translations:
            return

        messages.success(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} has successfully been translated ({source_language} ➜ {target_language}).",
                "The following {model_name} have successfully been translated ({source_language} ➜ {target_language}): {object_names}",
                len(self.successful_translations),
            ).format(
                model_name=ngettext(
                    self.model_name,
                    self.model_name_plural,
                    len(self.successful_translations),
                ),
                source_language=self.source_language,
                target_language=self.target_language,
                object_names=iter_to_string(
                    content_object.source_translation.title
                    for content_object in self.successful_translations
                ),
            ),
        )

    def alert_failed_translations(self) -> None:
        """
        Add messages informing the user about failed translations
        """
        if not self.failed_translations:
            return

        messages.success(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} could not be translated automatically.",
                "The following {model_name} could not translated automatically: {object_names}",
                len(self.failed_translations),
            ).format(
                model_name=ngettext(
                    self.model_name,
                    self.model_name_plural,
                    len(self.failed_translations),
                ),
                object_names=iter_to_string(self.failed_translations),
            ),
        )

    def alert_no_source_translation(self) -> None:
        """
        Add messages alerting the user that machine translation failed
        due to missing source translations
        """
        if not self.failed_because_no_source_translation:
            return

        messages.error(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} could not be translated because its source translation is missing.",
                "The following {model_name} could not be translated because their source translations are missing: {object_names}",
                len(self.failed_because_no_source_translation),
            ).format(
                model_name=ngettext(
                    self.model_name,
                    self.model_name_plural,
                    len(self.failed_because_no_source_translation),
                ),
                object_names=iter_to_string(
                    self.failed_because_no_source_translation,
                ),
            ),
        )

    def alert_insufficient_hix_score(self) -> None:
        """
        Add messages alerting the user that machine translation failed
        due to insufficient HIX scores
        """
        if not self.failed_because_insufficient_hix_score:
            return

        messages.error(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} could not be translated because its HIX score is too low for machine translation (minimum required: {min_required}).",
                "The following {model_name} could not be translated because their HIX score is too low for machine translation (minimum required: {min_required}): {object_names}",
                len(self.failed_because_insufficient_hix_score),
            ).format(
                model_name=ngettext(
                    self.model_name,
                    self.model_name_plural,
                    len(self.failed_because_insufficient_hix_score),
                ),
                object_names=iter_to_string(
                    self.failed_because_insufficient_hix_score,
                ),
                min_required=settings.HIX_REQUIRED_FOR_MT,
            ),
        )

    def alert_exceeds_limit(self) -> None:
        """
        Add messages alerting the user that machine translation failed
        due to insufficient translation budget
        """
        if not self.failed_because_exceeds_limit:
            return

        messages.error(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} could not be translated because it would exceed the remaining budget of {remaining_budget} words.",
                "The following {model_name} could not be translated because they would exceed the remaining budget of {remaining_budget} words: {object_names}",
                len(self.failed_because_exceeds_limit),
            ).format(
                model_name=ngettext(
                    self.model_name,
                    self.model_name_plural,
                    len(self.failed_because_exceeds_limit),
                ),
                remaining_budget=self.region.mt_budget_remaining,
                object_names=iter_to_string(
                    self.failed_because_exceeds_limit,
                ),
            ),
        )

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
