from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from google.cloud import (  # type: ignore[attr-defined]
    translate_v2,
    translate_v3,
)
from google.oauth2 import service_account

from ..core.utils.machine_translation_api_client import MachineTranslationApiClient
from ..core.utils.machine_translation_provider import MachineTranslationProvider

if TYPE_CHECKING:
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from integreat_cms.cms.models.languages.language import Language

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
            request.region,
            request.user,
            form_class._meta.model,
        ):
            raise RuntimeError(
                f'Machine translations are disabled for content type "{form_class._meta.model}" and {request.user!r}.',
            )
        if not settings.GOOGLE_TRANSLATE_ENABLED:
            raise RuntimeError("Google translate is disabled globally.")

        try:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS,
            )
            if settings.GOOGLE_TRANSLATE_VERSION == "Advanced":
                self.translator_v3 = translate_v3.TranslationServiceClient(
                    credentials=credentials,
                )
            else:
                self.translator_v2 = translate_v2.Client(credentials=credentials)
        except Exception:
            logger.exception(
                "Google translate is not available. Please check the credentials file.",
            )

    @staticmethod
    def get_target_language_key(target_language: Language) -> str:
        """
        This function decides the correct target language key

        :param target_language: the target language
        :return: target_language_key which is 2 characters long for all languages except English and Portuguese where the BCP tag is transmitted
        """
        google_translate_config = apps.get_app_config("google_translate_api")
        for code in [target_language.slug, target_language.bcp47_tag]:
            if code.lower() in google_translate_config.supported_target_languages:
                return code
        return ""

    def invoke_translation_api(self) -> None:
        """
        Translate all content objects stored in self.queryset using DeepL.
        """
        for content_object in self.queryset:
            data = {
                "status": content_object.source_translation.status,
                "machine_translated": True,
                "currently_in_translation": False,
                "title": content_object.source_translation.title,
            }

            for attr, attr_val in content_object.translatable_attributes:
                try:
                    # data has to be unescaped to recognize Umlaute
                    if settings.GOOGLE_TRANSLATE_VERSION == "Advanced":
                        mime_type = "text/html" if attr == "content" else "text/plain"
                        parent = settings.GOOGLE_PARENT_PARAM
                        request = translate_v3.TranslateTextRequest(
                            contents=[attr_val],
                            parent=parent,
                            target_language_code=self.target_language_key,
                            source_language_code=self.source_language.slug,
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
                            values=[attr_val],
                            target_language=self.target_language_key,
                            source_language=self.source_language.slug,
                            format_=format_,
                        )[0]["translatedText"]
                except Exception:
                    messages.error(
                        self.request,
                        _(
                            "A problem with Google Translate API has occurred. Please contact an administrator.",
                        ),
                    )
                    logger.exception("")
                    return

            self.save_translation(content_object, data)
