import logging
import deepl

from django.conf import settings
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.apps import apps

logger = logging.getLogger(__name__)


class DeepLApi:
    """
    DeepL API to auto translate selected posts.
    """

    def __init__(self):
        """
        Initialize the DeepL client
        """
        self.translator = deepl.Translator(settings.DEEPL_AUTH_KEY)

    @staticmethod
    def check_availability(request, language_slug):
        """
        This function checks, if the selected language is supported by DeepL

        :param request: request that was sent to the server
        :type request: ~django.http.HttpRequest

        :param language_slug: current language slug
        :type language_slug: str

        :return: true or false
        :rtype: bool
        """
        deepl_config = apps.get_app_config("deepl_api")
        source_language = request.region.get_source_language(language_slug)
        return (
            source_language
            and source_language.slug in deepl_config.supported_source_languages
            and language_slug in deepl_config.supported_target_languages
        )

    def deepl_translation(self, request, content_objects, language_slug, form_class):
        """
        This functions gets the translation from DeepL

        :param request: passed request
        :type request: ~django.http.HttpRequest

        :param content_objects: passed content objects
        :type content_objects: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]

        :param language_slug: current GUI language slug
        :type language_slug: str

        :param form_class: passed Form class of content type
        :type form_class: ~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm
        """
        # Get target language
        target_language = request.region.get_language_or_404(language_slug)
        source_language = request.region.get_source_language(language_slug)
        for content_object in content_objects:
            source_translation = content_object.get_translation(source_language.slug)
            if not source_translation:
                messages.error(
                    request,
                    _('No source translation could be found for {} "{}".').format(
                        type(content_object)._meta.verbose_name.title(),
                        content_object.best_translation.title,
                    ),
                )
                continue
            existing_target_translation = content_object.get_translation(
                target_language.slug
            )
            # For some languages, the DeepL client expects the BCP tag instead of the short language code
            if target_language.slug in ("en", "pt"):
                target_language_key = target_language.bcp47_tag
            else:
                target_language_key = target_language.slug
            target_title = self.translator.translate_text(
                source_translation.title,
                source_lang=source_language.slug,
                target_lang=target_language_key,
            )
            data = {
                "title": target_title,
                "status": existing_target_translation.status
                if existing_target_translation
                else source_translation.status,
            }
            if source_translation.content:
                data["content"] = self.translator.translate_text(
                    source_translation.content,
                    source_lang=source_language.slug,
                    target_lang=target_language_key,
                )
            # for pois adds a short description
            if hasattr(source_translation, "short_description"):
                data["short_description"] = self.translator.translate_text(
                    source_translation.short_description,
                    source_lang=source_language.slug,
                    target_lang=target_language_key,
                )
            content_translation_form = form_class(
                data=data,
                instance=existing_target_translation,
                additional_instance_attributes={
                    "creator": request.user,
                    "language": target_language,
                    source_translation.foreign_field(): content_object,
                },
            )
            # Validate event translation
            if content_translation_form.is_valid():
                content_translation_form.save()
                logger.debug(
                    "Successfully translated for: %r", content_translation_form.instance
                )
                messages.success(
                    request,
                    _('{} "{}" has been successfully translated.').format(
                        type(content_object)._meta.verbose_name.title(),
                        source_translation.title,
                    ),
                )
            else:
                logger.error(
                    "Automatic translation for %r could not be created because of %r",
                    content_object,
                    content_translation_form.errors,
                )
                messages.error(
                    request,
                    _('{} "{}" could not be automatically translated.').format(
                        type(content_object)._meta.verbose_name.title(),
                        source_translation.title,
                    ),
                )
