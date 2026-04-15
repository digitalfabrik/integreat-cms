from __future__ import annotations

import logging
from html import unescape
from typing import TYPE_CHECKING

import deepl
from deepl.exceptions import DeepLException
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from ..core.utils.machine_translation_api_client import (
    MachineTranslationApiClient,
    TranslationContext,
)
from ..core.utils.machine_translation_provider import MachineTranslationProvider

if TYPE_CHECKING:
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from integreat_cms.cms.models.languages.language import Language

    from .apps import DeepLApiClientConfig

logger = logging.getLogger(__name__)


class DeepLApiClient(MachineTranslationApiClient):
    """
    DeepL API client to automatically translate selected objects.
    """

    def __init__(self, request: HttpRequest, form_class: ModelFormMetaclass) -> None:
        """
        Initialize the DeepL client

        :param request: The current request
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

    def invoke_translation_api(self, context: list[TranslationContext]) -> None:
        """
        Translate all content objects (wrapped by TranslationContext) stored in context using DeepL.
        """
        deepl_config: DeepLApiClientConfig = apps.get_app_config("deepl_api")

        for ctx in context:
            if not ctx.source_translation:
                continue
            data: dict[str, bool | str | deepl.TextResult | list[deepl.TextResult]] = {
                "machine_translated": True,
            }

            for attr in self.translatable_fields:
                if getattr(ctx.existing_target_translation, attr, None):
                    data[attr] = unescape(
                        getattr(ctx.existing_target_translation, attr)
                    )

            if ctx.instance.do_not_translate_title:
                data["title"] = unescape(ctx.source_translation.title)

            if ctx.instance._meta.model_name != "pushnotification":
                data.update(
                    {
                        "status": ctx.source_translation.status,
                        "currently_in_translation": False,
                    }
                )

            for attr, attr_val in ctx.translatable_attributes:
                try:
                    # data has to be unescaped for DeepL to recognize Umlaute
                    glossary = deepl_config.get_glossary(
                        self.source_language.slug,
                        self.target_language_key,
                    )
                    logger.debug("Used glossary for translation: %s", glossary)
                    data[attr] = self.translator.translate_text(
                        unescape(attr_val),
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

            self.save_translation(ctx, data)
