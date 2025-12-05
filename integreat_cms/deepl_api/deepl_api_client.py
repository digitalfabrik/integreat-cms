from __future__ import annotations

import logging
from html import unescape
from typing import TYPE_CHECKING

import deepl
from celery import group, shared_task
from deepl.exceptions import DeepLException
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from ..core.utils.machine_translation_api_client import MachineTranslationApiClient
from ..core.utils.machine_translation_provider import MachineTranslationProvider

if TYPE_CHECKING:
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from integreat_cms.cms.models.languages.language import Language

    from .apps import DeepLApiClientConfig

logger = logging.getLogger(__name__)


def chunks(seq, size: int = 10):
    """
    Helper function to split ids list into chunks
    """
    if size <= 0:
        raise ValueError("Chunk size must be > 0")
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


@shared_task
def translate_queryset_async(
    ids_chunk,
    app_label,
    model_name,
    source_language_slug,
    target_language_key,
    form_module,
    form_name,
):
    translator = deepl.Translator(
        auth_key=settings.DEEPL_AUTH_KEY,
        server_url=settings.DEEPL_API_URL,
    )
    Model = apps.get_model(app_label, model_name)
    form_class = import_string(f"{form_module}.{form_name}")
    qs = Model.objects.filter(pk__in=ids_chunk)

    deepl_config: DeepLApiClientConfig = apps.get_app_config("deepl_api")

    for content_object in qs:
        data = {
            "status": content_object.source_translation.status,
            "machine_translated": True,
            "currently_in_translation": False,
            "title": unescape(content_object.source_translation.title),
        }

        for attr, attr_val in content_object.translatable_attributes:
            translate_attr(
                data,
                attr,
                attr_val,
                translator,
                deepl_config,
                source_language_slug,
                target_language_key,
            )
        save_translation_async(content_object, data, form_class, target_language_key)


def save_translation_async(content_object, data, form_class, target_language_key):
    content_translation_form = form_class(
        data=data,
        instance=content_object.existing_target_translation,
        additional_instance_attributes={
            "language": target_language_key,
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


def translate_attr(
    data,
    attr,
    attr_val,
    translator,
    deepl_config,
    source_language_slug,
    target_language_key,
):
    # data has to be unescaped for DeepL to recognize Umlaute
    glossary = deepl_config.get_glossary(
        source_language_slug,
        target_language_key,
    )
    logger.debug("Used glossary for translation: %s", glossary)
    data[attr] = translator.translate_text(
        unescape(attr_val),
        source_lang=source_language_slug,
        target_lang=target_language_key,
        tag_handling="html",
        glossary=glossary,
    )


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

    def invoke_translation_api(self, translate_async: bool = False) -> None:
        """
        Translate all content objects stored in self.queryset using DeepL.
        """
        if translate_async:
            app_label = self.queryset[0]._meta.app_label
            model_name = self.queryset[0]._meta.model_name
            ids = [x.id for x in self.queryset]
            job = group(
                translate_queryset_async.s(
                    ids_chunk,
                    app_label=app_label,
                    model_name=model_name,
                    source_language_slug=self.source_language.slug,
                    target_language_key=self.target_language_key,
                    form_module=self.form_class.__module__,
                    form_name=self.form_class.__name__,
                )
                for ids_chunk in chunks(ids)
            )
            job.apply_async()
            return

        deepl_config: DeepLApiClientConfig = apps.get_app_config("deepl_api")

        for content_object in self.queryset:
            data = {
                "status": content_object.source_translation.status,
                "machine_translated": True,
                "currently_in_translation": False,
                "title": unescape(content_object.source_translation.title),
            }

            for attr, attr_val in content_object.translatable_attributes:
                try:
                    translate_attr(
                        data,
                        attr,
                        attr_val,
                        self.translator,
                        deepl_config,
                        self.source_language.slug,
                        self.target_language_key,
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
