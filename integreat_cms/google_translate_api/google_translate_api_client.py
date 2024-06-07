from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from google.cloud import translate_v2, translate_v3  # type: ignore[attr-defined]
from google.oauth2 import service_account

from ..cms.utils.stringify_list import iter_to_string
from ..core.utils.machine_translation_api_client import MachineTranslationApiClient
from ..core.utils.machine_translation_provider import MachineTranslationProvider
from ..textlab_api.utils import check_hix_score

if TYPE_CHECKING:
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from integreat_cms.cms.models.events.event import Event
    from integreat_cms.cms.models.languages.language import Language
    from integreat_cms.cms.models.pages.page import Page
    from integreat_cms.cms.models.pois.poi import POI

logger = logging.getLogger(__name__)


class GoogleTranslateApiClient(MachineTranslationApiClient):
    """
    Google Translate API client to automatically translate selected objects.
    """

    def __init__(self, request: HttpRequest, form_class: ModelFormMetaclass) -> None:
        """
        Initialize the Google Translate client

        :param region: The current region
        :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                           subclass of the current content type
        """
        super().__init__(request, form_class)
        if not MachineTranslationProvider.is_permitted(
            request.region, request.user, form_class._meta.model
        ):
            raise RuntimeError(
                f'Machine translations are disabled for content type "{form_class._meta.model}" and {request.user!r}.'
            )
        if not settings.GOOGLE_TRANSLATE_ENABLED:
            raise RuntimeError("Google translate is disabled globally.")

        try:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            if settings.GOOGLE_TRANSLATE_VERSION == "Advanced":
                self.translator_v3 = translate_v3.TranslationServiceClient(
                    credentials=credentials
                )
            else:
                self.translator_v2 = translate_v2.Client(credentials=credentials)
        except Exception as e:  # pylint: disable=broad-except
            logger.error(e)
            logger.error(
                "Google translate is not available. Please check the credentials file."
            )

    @staticmethod
    def get_target_language_key(target_language: Language) -> str:
        """
        This function decides the correct target language key

        :param target_language: the target language
        :return: target_language_key which is 2 characters long for all languages except English and Portugese where the BCP tag is transmitted
        """
        google_translate_config = apps.get_app_config("google_translate_api")
        for code in [target_language.slug, target_language.bcp47_tag]:
            if code.lower() in google_translate_config.supported_target_languages:
                return code
        return ""

    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    def translate_queryset(  # noqa: PLR0915
        self, queryset: list[Event] | (list[Page] | list[POI]), language_slug: str
    ) -> None:
        """
        This function translates a content queryset via Google Translate

        :param queryset: The content QuerySet
        :param language_slug: The target language slug
        """
        with transaction.atomic():
            # Re-select the region from db to prevent simultaneous
            # requests exceeding the MT usage limit
            region = (
                apps.get_model("cms", "Region")
                .objects.select_for_update()
                .get(id=self.request.region.id)
            )
            # Get target language
            target_language = region.get_language_or_404(language_slug)
            source_language = region.get_source_language(language_slug)

            target_language_key = self.get_target_language_key(target_language)

            failed_changes_because_no_source_translation = []
            failed_changes_because_exceeds_limit = []
            failed_changes_because_insufficient_hix_score = []
            failed_changes_generic_error = []
            successful_changes = []

            google_translate_api_error = False

            for content_object in queryset:
                source_translation = content_object.get_translation(
                    source_language.slug
                )
                if not source_translation:
                    failed_changes_because_no_source_translation.append(
                        content_object.best_translation.title
                    )
                    continue

                if not check_hix_score(
                    self.request, source_translation, show_message=False
                ):
                    failed_changes_because_insufficient_hix_score.append(
                        source_translation.title
                    )
                    continue

                existing_target_translation = content_object.get_translation(
                    target_language.slug
                )

                # Before translating, check if translation would exceed usage limit
                (
                    translation_exceeds_limit,
                    word_count,
                ) = self.check_usage(region, source_translation)
                if translation_exceeds_limit:
                    failed_changes_because_exceeds_limit.append(
                        source_translation.title
                    )
                    continue

                data = {
                    "status": source_translation.status,
                    "machine_translated": True,
                    "currently_in_translation": False,
                }

                for attr in self.translatable_attributes:
                    # Only translate existing, non-empty attributes
                    if hasattr(source_translation, attr) and getattr(
                        source_translation, attr
                    ):
                        try:
                            # data has to be unescaped to recognize Umlaute
                            if settings.GOOGLE_TRANSLATE_VERSION == "Advanced":
                                mime_type = (
                                    "text/html" if attr == "content" else "text/plain"
                                )
                                parent = settings.GOOGLE_PARENT_PARAM
                                request = translate_v3.TranslateTextRequest(
                                    contents=[getattr(source_translation, attr)],
                                    parent=parent,
                                    target_language_code=target_language_key,
                                    source_language_code=source_language.slug,
                                    mime_type=mime_type,
                                )
                                data[attr] = (
                                    self.translator_v3.translate_text(request=request)
                                    .translations[0]
                                    .translated_text
                                )
                            else:
                                format_ = "html" if attr == "content" else "text"
                                data[attr] = self.translator_v2.translate(
                                    values=[getattr(source_translation, attr)],
                                    target_language=target_language_key,
                                    source_language=source_language.slug,
                                    format_=format_,
                                )[0]["translatedText"]
                        except Exception as e:  # pylint: disable=broad-except
                            google_translate_api_error = True
                            logger.error(e)
                            break

                content_translation_form = self.form_class(
                    data=data,
                    instance=existing_target_translation,
                    additional_instance_attributes={
                        "creator": self.request.user,
                        "language": target_language,
                        source_translation.foreign_field(): content_object,
                    },
                )
                # Validate content translation
                if content_translation_form.is_valid():
                    content_translation_form.save()
                    # Revert "currently in translation" value of all versions
                    if existing_target_translation:
                        if settings.REDIS_CACHE:
                            existing_target_translation.all_versions.invalidated_update(
                                currently_in_translation=False
                            )
                        else:
                            existing_target_translation.all_versions.update(
                                currently_in_translation=False
                            )

                    logger.debug(
                        "Successfully translated for: %r",
                        content_translation_form.instance,
                    )
                    successful_changes.append(source_translation.title)
                else:
                    logger.error(
                        "Automatic translation for %r could not be created because of %r",
                        content_object,
                        content_translation_form.errors,
                    )
                    failed_changes_generic_error.append(source_translation.title)

                # Update remaining MT usage for the region
                region.mt_budget_used += word_count
                region.save()

            if queryset:
                meta = type(queryset[0])._meta
                model_name = meta.verbose_name.title()
                model_name_plural = meta.verbose_name_plural
            else:
                model_name = model_name_plural = ""

            if successful_changes:
                messages.success(
                    self.request,
                    ngettext_lazy(
                        "{model_name} {object_names} has successfully been translated ({source_language} ➜ {target_language}).",
                        "The following {model_name_plural} have successfully been translated ({source_language} ➜ {target_language}): {object_names}",
                        len(successful_changes),
                    ).format(
                        model_name=model_name,
                        model_name_plural=model_name_plural,
                        source_language=source_language,
                        target_language=target_language,
                        object_names=iter_to_string(successful_changes),
                    ),
                )

            if failed_changes_because_no_source_translation:
                messages.error(
                    self.request,
                    ngettext_lazy(
                        "{model_name} {object_names} could not be translated because its source translation is missing.",
                        "The following {model_name_plural} could not be translated because their source translations are missing: {object_names}",
                        len(failed_changes_because_exceeds_limit),
                    ).format(
                        model_name=model_name,
                        model_name_plural=model_name_plural,
                        object_names=iter_to_string(
                            failed_changes_because_no_source_translation
                        ),
                    ),
                )

            if failed_changes_because_exceeds_limit:
                messages.error(
                    self.request,
                    ngettext_lazy(
                        "{model_name} {object_names} could not be translated because it would exceed the remaining budget of {remaining_budget} words.",
                        "The following {model_name_plural} could not be translated because they would exceed the remaining budget of {remaining_budget} words: {object_names}",
                        len(failed_changes_because_exceeds_limit),
                    ).format(
                        model_name=model_name,
                        model_name_plural=model_name_plural,
                        remaining_budget=region.mt_budget_remaining,
                        object_names=iter_to_string(
                            failed_changes_because_exceeds_limit
                        ),
                    ),
                )

            if failed_changes_because_insufficient_hix_score:
                messages.error(
                    self.request,
                    ngettext_lazy(
                        "{model_name} {object_names} could not be translated because its HIX score is too low for machine translation (minimum required: {min_required}).",
                        "The following {model_name_plural} could not be translated because their HIX score is too low for machine translation (minimum required: {min_required}): {object_names}",
                        len(failed_changes_because_insufficient_hix_score),
                    ).format(
                        model_name=model_name,
                        model_name_plural=model_name_plural,
                        min_required=settings.HIX_REQUIRED_FOR_MT,
                        object_names=iter_to_string(
                            failed_changes_because_insufficient_hix_score
                        ),
                    ),
                )

            if failed_changes_generic_error:
                messages.error(
                    self.request,
                    ngettext_lazy(
                        "{model_name} {object_names} could not be translated automatically.",
                        "The following {model_name_plural} could not translated automatically: {object_names}",
                        len(failed_changes_generic_error),
                    ).format(
                        model_name=model_name,
                        model_name_plural=model_name_plural,
                        object_names=iter_to_string(failed_changes_generic_error),
                    ),
                )

            if google_translate_api_error:
                messages.error(
                    self.request,
                    _(
                        "A problem with Google Translate API has occurred. Please contact an administrator."
                    ),
                )
