"""
This module contains utilities for machine translation API clients
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.utils.translation import gettext, ngettext

from ...cms.constants.machine_translatable_fields import TRANSLATABLE_FIELDS
from ...cms.constants.machine_translation_budget import MINIMAL
from ...cms.models.abstract_content_translation import AbstractContentTranslation
from ...cms.utils.stringify_list import iter_to_string
from ...textlab_api.utils import check_hix_score
from .word_count import word_count

if TYPE_CHECKING:
    from typing import Any

    from django.forms.models import ModelFormMetaclass
    from django.forms.utils import ErrorDict
    from django.http import HttpRequest
    from django.utils.functional import Promise

    from ...cms.models import (
        Language,
        Region,
    )
    from ...cms.models.abstract_content_model import AbstractContentModel


logger = logging.getLogger(__name__)


@dataclass
class TranslationContext:
    instance: AbstractContentModel
    source_translation: AbstractContentTranslation | None = None
    existing_target_translation: AbstractContentTranslation | None = None
    translatable_attributes: list[tuple[str, str]] = field(default_factory=list)
    word_count: int = 0


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
    successful_translations: list[TranslationContext] = []
    refreshed_translations: list[TranslationContext] = []
    #: Translations with an attached API failure
    failed_translations: list[str] = []
    #: Content objects untranslatable since no actual changes were made
    failed_because_no_changes_made: list[str] = []
    #: Content objects untranslatable due to missing source translations
    failed_because_no_source_translation: list[str] = []
    #: Content objects untranslatable due to too-low hix score
    failed_because_insufficient_hix_score: list[str] = []
    #: Content objects untranslatable due to insufficient translation budget
    failed_because_exceeds_limit: list[str] = []
    #: Content objects untranslatable due to too long text (only applies for push notification translation)
    failed_because_too_long_text: list[str] = []
    #: Max length of "text" of Push Notification Translation
    max_text_length: int | None = None

    def __init__(self, request: HttpRequest, form_class: ModelFormMetaclass) -> None:
        """
        Constructor initializes the class variables

        :param request: The current request
        :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                           subclass of the current content type
        """
        self.request = request
        self.region = request.region
        self.form_class = form_class
        self.translatable_fields = TRANSLATABLE_FIELDS

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
        self.refreshed_translations = []
        self.failed_translations = []
        self.failed_because_no_changes_made = []
        self.failed_because_no_source_translation = []
        self.failed_because_insufficient_hix_score = []
        self.failed_because_exceeds_limit = []
        self.failed_because_too_long_text = []

    @abstractmethod
    def invoke_translation_api(self, context: list[TranslationContext]) -> None:
        """
        Translate all ctx.instance stored in context.
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

    def translate_object(self, obj: AbstractContentModel, language_slug: str) -> None:
        """
        This function translates one content object

        :param obj: The content object
        :param language_slug: The target language slug
        """
        return self.translate_queryset([obj], language_slug)

    @transaction.atomic
    def translate_queryset(
        self,
        queryset: list[AbstractContentModel],
        language_slug: str,
    ) -> None:
        """
        This function translates a content queryset via the configured machine translation provider.

        Content objects are wrapped into :class:`TranslationContext` instances, filtered
        for translatability, and then passed to the provider-specific translation API.

        :param queryset: The content QuerySet
        :param language_slug: The target language slug
        """
        if not queryset:
            return

        self.reset()

        # Re-select the region from db to prevent simultaneous
        # requests exceeding the machine translation usage limit
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
        context = self.prepare_content_objects()
        context = self.filter_no_source_translation(context)
        context = self.filter_unchanged_translations(context)
        context = self.filter_insufficient_hix_score(context)
        context = self.filter_exceeds_limit(context)

        # Provider-API-specific implementation
        self.invoke_translation_api(context)

        # Update remaining budget of the region
        region.mt_budget_used += sum(
            ctx.word_count for ctx in self.successful_translations
        )
        region.save()

    def filter_unchanged_translations(
        self, context: list[TranslationContext]
    ) -> list[TranslationContext]:
        """
        This method filters out entries from the context list if there have
        been no changes made to the source_translation.

        If there are no changes but the target translation is outdated, a new
        translation version is created with ``minor_edit=True`` to refresh its
        status without flagging it as a content change, instead of being
        recorded as a plain "no changes made" failure.

        Push notifications are excluded from the refresh case because they do
        not use ``AbstractContentTranslation`` and therefore have no outdated
        status to refresh.

        The removed entries are stored in order to show users batched
        messages after all objects have been handled.

        :param context: The list of translation contexts to filter
        :return: The filtered list of translation contexts
        """
        filtered_context = []

        for ctx in context:
            if bool(ctx.translatable_attributes):
                filtered_context.append(ctx)
                continue

            target_translation = ctx.existing_target_translation
            if (
                isinstance(target_translation, AbstractContentTranslation)
                # `is_outdated` treats a translation currently being worked on
                # as not outdated at all - correct for display, but wrong
                # here: this task set that very flag on this very
                # translation before it started, so it would otherwise
                # always see "not outdated" about itself.
                and target_translation.is_content_outdated
            ):
                target_translation.save_new_version(self.request.user)
                self.refreshed_translations.append(ctx)
            else:
                self.failed_because_no_changes_made.append(
                    ctx.instance.best_translation.title
                )

        return filtered_context

    def filter_no_source_translation(
        self, context: list[TranslationContext]
    ) -> list[TranslationContext]:
        """
        This method filters out entries from the context list
        if they do not have the required source translation.

        The removed entries are stored in order to show users
        batched error messages after all objects have been handled.

        :param context: The list of translation contexts to filter
        :return: The filtered list of translation contexts
        """
        filtered_context = []

        for ctx in context:
            if ctx.source_translation:
                filtered_context.append(ctx)
            else:
                self.failed_because_no_source_translation.append(
                    ctx.instance.best_translation.title
                )

        return filtered_context

    def filter_insufficient_hix_score(
        self, context: list[TranslationContext]
    ) -> list[TranslationContext]:
        """
        This method filters out entries from the context list
        if they do not have the required HIX score.

        The removed entries are stored in order to show users
        batched error messages after all objects have been handled.

        :param context: The list of translation contexts to filter
        :return: The filtered list of translation contexts
        """
        filtered_context = []

        for ctx in context:
            if not ctx.source_translation:
                logger.debug(
                    "No source translation available for %r. Will be automatically filtered out",
                    ctx,
                )
                continue
            if check_hix_score(
                self.request,
                ctx.source_translation,
                show_message=False,
            ):
                filtered_context.append(ctx)
            else:
                self.failed_because_insufficient_hix_score.append(
                    ctx.source_translation.title
                )

        return filtered_context

    def filter_exceeds_limit(
        self, context: list[TranslationContext]
    ) -> list[TranslationContext]:
        """
        This method filters out entries from the context list
        if translating them would exceed the translation budget.

        The removed entries are stored in order to show users
        batched error messages after all objects have been handled.

        :param context: The list of translation contexts to filter
        :return: The filtered list of translation contexts
        """
        remaining_budget = self.region.mt_budget_remaining
        filtered_context = []

        for ctx in context:
            if not ctx.source_translation:
                logger.debug(
                    "No source translation available for %r. Will be automatically filtered out",
                    ctx,
                )
                continue
            if (
                max(
                    1,
                    ctx.word_count - settings.MT_SOFT_MARGIN_FRACTION * MINIMAL,
                )
                < remaining_budget
            ):
                filtered_context.append(ctx)
                remaining_budget -= ctx.word_count
            else:
                self.failed_because_exceeds_limit.append(ctx.source_translation.title)

        return filtered_context

    def prepare_content_objects(self) -> list[TranslationContext]:
        """
        Wrap each content object in a :class:`TranslationContext` and
        populate it with pre-computed translation metadata (source/target
        translations, translatable attributes, word count).

        :return: A list of :class:`TranslationContext` instances ready for filtering
        """
        context = []
        for content_object in self.queryset:
            ctx = TranslationContext(instance=content_object)
            ctx.source_translation = content_object.get_translation(
                self.source_language.slug,
            )
            ctx.existing_target_translation = content_object.get_translation(
                self.target_language.slug,
            )
            try:
                if hasattr(content_object, "get_translatable_attributes"):
                    ctx.translatable_attributes = (
                        content_object.get_translatable_attributes(
                            self.translatable_fields,
                            self.source_language.slug,
                            self.target_language.slug,
                        )
                    )
                else:
                    # push_notifications do not have the get_translatable_attributes logic, so we need to provide a fallback
                    skip_title = getattr(
                        content_object, "do_not_translate_title", False
                    )
                    ctx.translatable_attributes = [
                        (attr, getattr(ctx.source_translation, attr))
                        for attr in self.translatable_fields
                        if ctx.source_translation
                        and getattr(ctx.source_translation, attr, None)
                        and not (attr == "title" and skip_title)
                    ]

                ctx.word_count = word_count(
                    ctx.translatable_attributes,
                )
            except ValueError:
                pass  # will be caught by .filter_no_source_translation() later

            context.append(ctx)
        return context

    def mark_successful(self, ctx: TranslationContext) -> None:
        """
        Mark a content object as having been translated successfully
        """
        logger.debug(
            "Successfully translated for: %r",
            ctx.existing_target_translation,
        )
        self.successful_translations.append(ctx)

    def mark_unsuccessful(
        self, ctx: TranslationContext, errors: ErrorDict | Exception
    ) -> None:
        """
        Mark a translation as unsuccessful (usually due to API errors)
        """
        if not ctx.source_translation:
            logger.debug(
                "No source translation available for %r. Cannot be marked as unsuccessful",
                ctx,
            )
            return
        logger.error(
            "Automatic translation for %r could not be created because of %r",
            ctx,
            errors,
        )
        self.failed_translations.append(ctx.source_translation.title)

    def mark_too_long(
        self, ctx: TranslationContext, errors: ErrorDict | Exception
    ) -> None:
        """
        Mark a translation as too long
        """
        if not ctx.source_translation:
            logger.debug(
                "No source translation available for %r. Cannot be marked as too long",
                ctx,
            )
            return
        logger.error(
            "Automatic translation for %r could not be created because of %r",
            ctx,
            errors,
        )
        self.failed_because_too_long_text.append(ctx.source_translation.title)

    def save_translation(self, ctx: TranslationContext, translation_data: dict) -> None:
        """
        Create a translation form based on the extracted content object data,
        save it, and validate the translation.
        """
        if not ctx.source_translation:
            logger.debug(
                "No source translation available for %r. Cannot be translated", ctx
            )
            return
        attributes = {
            "language": self.target_language,
        }
        if ctx.instance._meta.model_name != "pushnotification":
            attributes.update(
                {
                    "creator": self.request.user,
                    ctx.source_translation.foreign_field(): ctx.instance,
                }
            )
        else:
            attributes.update(
                {
                    "push_notification": ctx.instance,
                }
            )
        content_translation_form = self.form_class(
            data=translation_data,
            instance=ctx.existing_target_translation,
            additional_instance_attributes=attributes,
        )

        # Validate content translation
        if content_translation_form.is_valid():
            content_translation_form.save()
            # Revert "currently in translation" value of all versions
            if (
                ctx.instance._meta.model_name != "pushnotification"
                and ctx.existing_target_translation
            ):
                if settings.REDIS_CACHE:
                    ctx.existing_target_translation.all_versions.invalidated_update(
                        currently_in_translation=False,
                    )
                else:
                    ctx.existing_target_translation.all_versions.update(
                        currently_in_translation=False,
                    )

            self.mark_successful(ctx)
        elif content_translation_form.has_error("text", code="max_length"):
            self.max_text_length = content_translation_form.instance._meta.get_field(
                "text"
            ).max_length
            self.mark_too_long(ctx, content_translation_form.errors)
        else:
            self.mark_unsuccessful(ctx, content_translation_form.errors)

    def _format_message(
        self,
        message: str | Promise,
        items: list,
        **extra_kwargs: Any,
    ) -> str:
        return str(message).format(
            model_name=ngettext(self.model_name, self.model_name_plural, len(items)),
            object_names=iter_to_string(items),
            **extra_kwargs,
        )

    def get_refreshed_translations_message(self) -> str:
        items = [
            ctx.source_translation.title
            for ctx in self.refreshed_translations
            if ctx.source_translation is not None
        ]
        if not items:
            return ""
        message = ngettext(
            "{model_name} {object_names}: Translation into '{target_language}' was not necessary -> no changes detected. The translation date has been refreshed.",
            "{model_name} {object_names}: Translation into '{target_language}' was not necessary -> no changes detected. The translation dates have been refreshed.",
            len(items),
        )
        return self._format_message(
            message, items, target_language=self.target_language
        )

    def get_successful_translation_message(self) -> str:
        items = [
            ctx.source_translation.title
            for ctx in self.successful_translations
            if ctx.source_translation is not None
        ]
        if not items:
            return ""
        message = ngettext(
            "{model_name} {object_names} has successfully been translated ({source_language} ➜ {target_language}).",
            "The following {model_name} have successfully been translated ({source_language} ➜ {target_language}): {object_names}",
            len(items),
        )
        return self._format_message(
            message,
            items,
            source_language=self.source_language,
            target_language=self.target_language,
        )

    def get_failed_translation_message(self) -> str:
        items = self.failed_translations
        if not items:
            return ""
        message = ngettext(
            "{model_name} {object_names} could not be translated automatically into '{target_language}'",
            "The following {model_name} could not be translated automatically into '{target_language}': {object_names}",
            len(items),
        )
        return self._format_message(
            message, items, target_language=self.target_language
        )

    def get_no_changes_made_message(self) -> str:
        items = self.failed_because_no_changes_made
        if not items:
            return ""
        message = ngettext(
            "{model_name} {object_names} was not translated into '{target_language}', because there were no changes to the source translation.",
            "The following {model_name} were not translated into '{target_language}', because there were no changes to the source translation: {object_names}",
            len(items),
        )
        return self._format_message(
            message, items, target_language=self.target_language
        )

    def get_no_source_translation_message(self) -> str:
        items = self.failed_because_no_source_translation
        if not items:
            return ""
        message = ngettext(
            "{model_name} {object_names} could not be translated because its source translation is missing.",
            "The following {model_name} could not be translated because their source translations are missing: {object_names}",
            len(items),
        )
        return self._format_message(message, items)

    def get_insufficient_hix_score_message(self) -> str:
        items = self.failed_because_insufficient_hix_score
        if not items:
            return ""
        message = ngettext(
            "{model_name} {object_names} could not be translated because its HIX score is too low for machine translation (minimum required: {min_required}).",
            "The following {model_name} could not be translated because their HIX score is too low for machine translation (minimum required: {min_required}): {object_names}",
            len(items),
        )
        return self._format_message(
            message, items, min_required=settings.HIX_REQUIRED_FOR_MT
        )

    def get_exceeds_limit_message(self) -> str:
        items = self.failed_because_exceeds_limit
        if not items:
            return ""
        message = ngettext(
            "{model_name} {object_names} could not be translated because it would exceed the remaining budget of {remaining_budget} words.",
            "The following {model_name} could not be translated because they would exceed the remaining budget of {remaining_budget} words: {object_names}",
            len(items),
        )
        return self._format_message(
            message, items, remaining_budget=self.region.mt_budget_remaining
        )

    def get_too_long_text_message(self) -> str:
        if not self.failed_because_too_long_text:
            return ""
        message = gettext(
            "{model_name} {object_names} could not be translated because the generated translation ({source_language} ➜ {target_language}) exceeded the {max_text_length} character limit."
        )
        return str(message).format(
            model_name=self.model_name,
            object_names=iter_to_string(self.failed_because_too_long_text),
            source_language=self.source_language,
            target_language=self.target_language,
            max_text_length=self.max_text_length,
        )

    def alert_refreshed_translations(self) -> None:
        if not self.refreshed_translations:
            return
        messages.info(self.request, self.get_refreshed_translations_message())

    def alert_successful_translations(self) -> None:
        if not self.successful_translations:
            return
        messages.success(self.request, self.get_successful_translation_message())

    def alert_failed_translations(self) -> None:
        if not self.failed_translations:
            return
        messages.error(self.request, self.get_failed_translation_message())

    def alert_no_changes_made(self) -> None:
        if not self.failed_because_no_changes_made:
            return
        messages.error(self.request, self.get_no_changes_made_message())

    def alert_no_source_translation(self) -> None:
        if not self.failed_because_no_source_translation:
            return
        messages.error(self.request, self.get_no_source_translation_message())

    def alert_insufficient_hix_score(self) -> None:
        if not self.failed_because_insufficient_hix_score:
            return
        messages.error(self.request, self.get_insufficient_hix_score_message())

    def alert_exceeds_limit(self) -> None:
        if not self.failed_because_exceeds_limit:
            return
        messages.error(self.request, self.get_exceeds_limit_message())

    def alert_too_long_text(self) -> None:
        if not self.failed_because_too_long_text:
            return
        messages.error(self.request, self.get_too_long_text_message())

    def alert_messages(self) -> None:
        self.alert_successful_translations()
        self.alert_refreshed_translations()
        self.alert_failed_translations()
        self.alert_no_changes_made()
        self.alert_no_source_translation()
        self.alert_insufficient_hix_score()
        self.alert_exceeds_limit()
        self.alert_too_long_text()

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
