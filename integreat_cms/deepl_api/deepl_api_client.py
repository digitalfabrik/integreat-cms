from __future__ import annotations

import logging
from html import unescape
from typing import TYPE_CHECKING

import deepl
from deepl.exceptions import DeepLException
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from ..cms.utils.stringify_list import iter_to_string
from ..core.utils.machine_translation_api_client import MachineTranslationApiClient
from ..core.utils.machine_translation_provider import MachineTranslationProvider
from ..core.utils.word_count import word_count
from ..textlab_api.utils import check_hix_score

if TYPE_CHECKING:
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from integreat_cms.cms.models.events.event import Event
    from integreat_cms.cms.models.languages.language import Language
    from integreat_cms.cms.models.pages.page import Page
    from integreat_cms.cms.models.pois.poi import POI

    from .apps import DeepLApiClientConfig

logger = logging.getLogger(__name__)


class DeepLApiClient(MachineTranslationApiClient):
    """
    DeepL API client to automatically translate selected objects.
    """

    def __init__(self, request: HttpRequest, form_class: ModelFormMetaclass) -> None:
        """
        Initialize the DeepL client

        :param region: The current region
        :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                           subclass of the current content type
        """
        super().__init__(request, form_class)
        if not MachineTranslationProvider.is_permitted(
            request.region,
            request.user,
            form_class._meta.model,
        ):
            raise RuntimeError(
                f'Machine translations are disabled for content type "{form_class._meta.model}" and {request.user!r}.',
            )
        if not settings.DEEPL_ENABLED:
            raise RuntimeError("DeepL is disabled globally.")
        self.translator = deepl.Translator(
            auth_key=settings.DEEPL_AUTH_KEY,
            server_url=settings.DEEPL_API_URL,
        )

    @staticmethod
    def get_target_language_key(target_language: Language) -> str:
        """
        This function decides the correct target language key

        :param target_language: the target language
        :return: target_language_key which is 2 characters long for all languages except English and Portuguese where the BCP tag is transmitted
        """
        deepl_config = apps.get_app_config("deepl_api")
        for code in [target_language.slug, target_language.bcp47_tag]:
            if code.lower() in deepl_config.supported_target_languages:
                return code
        return ""

    def filter_no_source_translation(self):
        """
        This method removes content objects from the main queryset
        if they do not have the required source translation.

        The removed elements are stored in order to show users
        batched error messages after all objects have been handled.

        :param source_language: The source language slug
        """
        self.queryset[:] = [
            content_object
            for content_object in self.queryset
            if content_object.source_translation
            or self.failed_changes_because_no_source_translation.append(
                content_object.best_translation.title
            )
        ]

    def filter_insufficient_hix_score(self):
        """
        This method removes content objects from the main queryset
        if they do not have the required HIX score.

        The removed elements are stored in order to show users
        batched error messages after all objects have been handled.

        :param source_language: The source language slug
        """
        self.queryset[:] = [
            content_object
            for content_object in self.queryset
            if check_hix_score(
                self.request,
                self.source_translation,
                show_message=False,
            )
            or self.failed_changes_because_insufficient_hix_score.append(
                content_object.source_translation.title
            )
        ]

    def filter_exceeds_limit(self):
        """
        This method removes content objects from the main queryset
        if translating them would exceed the translation budget.

        The removed elements are stored in order to show users
        batched error messages after all objects have been handled.

        :param source_language: The source language slug
        """
        remaining_budget = self.remaining_budget()
        filtered_queryset = []

        for content_object in self.queryset:
            if content_object.word_count:
                filtered_queryset.append(content_object)
                remaining_budget -= content_object.word_count
            else:
                self.failed_changes_because_exceeds_limit.append(
                    content_object.source_translation.title
                )

        self.queryset[:] = filtered_queryset

    def prepare_content_objects(self):
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
            content_object.word_count = word_count(content_object.source_translation)
            content_object.translatable_attributes = [
                (attr, unescape(getattr(content_object.source_translation, attr)))
                for attr in self.translatable_attributes
                if hasattr(content_object.source_translation, attr)
                and getattr(content_object.source_translation, attr)
            ]

    def mark_successful(self, content_object: Event | Page | POI):
        """
        Mark a content object as having been translated successfully
        """
        logger.debug(
            "Successfully translated for: %r",
            content_object.existing_target_translation,
        )
        self.successful_translations.append(content_object.source_translation.title)

    def mark_unsuccessful(self, content_object: Event | Page | POI, errors: bool):
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
    ):
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

    def invoke_translation_api(self):
        """
        Translate all content objects stored in self.queryset.

        This method is only meant for internal use in the machine learning API clients,
        since no pre-processing or error handling is performed inside it.

        It must be implemented for each machine learning API individually.
        """
        deepl_config: DeepLApiClientConfig = apps.get_app_config("deepl_api")

        for content_object in self.queryset:
            data = {
                "status": content_object.source_translation.status,
                "machine_translated": True,
                "currently_in_translation": False,
            }

            for attr, attr_val in content_object.translatable_attributes:
                try:
                    # data has to be unescaped for DeepL to recognize Umlaute
                    glossary = deepl_config.get_glossary(
                        self.source_language.slug,
                        self.target_language_key,
                    )
                    logger.debug("Used glossary for translation: %s", glossary)
                    data[attr] = self.translator.translate_text(
                        attr_val,
                        source_lang=self.source_language.slug,
                        target_lang=self.target_language_key,
                        tag_handling="html",
                        glossary=glossary,
                    )
                except DeepLException:
                    messages.error(
                        self.request,
                        _(
                            "A problem with DeepL API has occurred. Please contact an administrator.",
                        ),
                    )
                    logger.exception("")
                    return

            self.save_translation(content_object, data)

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
        meta = type(queryset[0])._meta
        self.model_name = meta.verbose_name.title()
        self.model_name_plural = meta.verbose_name_plural

        self.alert_successful_translations()
        self.alert_failed_translations()
        self.alert_no_source_translation()
        self.alert_insufficient_hix_score()
        self.alert_exceeds_limit()

    def alert_successful_translations(self):
        """
        Add messages informing the user about successful translations
        """
        if not self.successful_translations:
            return

        messages.success(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} has successfully been translated ({source_language} ➜ {target_language}).",
                "The following {model_name_plural} have successfully been translated ({source_language} ➜ {target_language}): {object_names}",
                len(self.successful_translations),
            ).format(
                model_name=self.model_name,
                model_name_plural=self.model_name_plural,
                source_language=self.source_language,
                target_language=self.target_language,
                object_names=iter_to_string(self.successful_translations),
            ),
        )

    def alert_failed_translations(self):
        """
        Add messages informing the user about failed translations
        """
        if not self.failed_translations:
            return

        messages.success(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} could not be translated automatically.",
                "The following {model_name_plural} could not translated automatically: {object_names}",
                len(self.failed_translations),
            ).format(
                model_name=self.model_name,
                model_name_plural=self.model_name_plural,
                object_names=iter_to_string(self.failed_translations),
            ),
        )

    def alert_no_source_translation(self):
        """
        Add messages alerting the user that machine translation failed
        due to missing source translations
        """
        if not self.failed_changes_because_no_source_translation:
            return

        messages.error(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} could not be translated because its source translation is missing.",
                "The following {model_name_plural} could not be translated because their source translations are missing: {object_names}",
                len(self.failed_changes_because_no_source_translation),
            ).format(
                model_name=self.model_name,
                model_name_plural=self.model_name_plural,
                object_names=iter_to_string(
                    self.failed_changes_because_no_source_translation,
                ),
            ),
        )

    def alert_insufficient_hix_score(self):
        """
        Add messages alerting the user that machine translation failed
        due to insufficient HIX scores
        """
        if not self.failed_changes_because_insufficient_hix_score:
            return

        messages.error(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} could not be translated because its HIX score is too low for machine translation (minimum required: {min_required}).",
                "The following {model_name_plural} could not be translated because their HIX score is too low for machine translation (minimum required: {min_required}): {object_names}",
                len(self.failed_changes_because_insufficient_hix_score),
            ).format(
                model_name=self.model_name,
                model_name_plural=self.model_name_plural,
                object_names=iter_to_string(
                    self.failed_changes_because_insufficient_hix_score,
                ),
            ),
        )

    def alert_exceeds_limit(self):
        """
        Add messages alerting the user that machine translation failed
        due to insufficient translation budget
        """
        if not self.failed_changes_because_exceeds_limit:
            return

        messages.error(
            self.request,
            ngettext_lazy(
                "{model_name} {object_names} could not be translated because it would exceed the remaining budget of {remaining_budget} words.",
                "The following {model_name_plural} could not be translated because they would exceed the remaining budget of {remaining_budget} words: {object_names}",
                len(self.failed_changes_because_exceeds_limit),
            ).format(
                model_name=self.model_name,
                model_name_plural=self.model_name_plural,
                object_names=iter_to_string(
                    self.failed_changes_because_exceeds_limit,
                ),
            ),
        )
