from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django import forms
from django.utils.translation import gettext_lazy as _

from ...models import LanguageTreeNode, Region
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any, Iterator

    from ....core.utils.machine_translation_provider import (
        MachineTranslationProviderType,
    )

logger = logging.getLogger(__name__)


class CustomCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Custom CheckboxSelectMultiple child class which appends a machine
    translation provider to option labels or disables them if no provider
    is available
    """

    #: The template to use when rendering this widget
    template_name: str = "translations/languages_input.html"


@dataclass
class TranslationLanguageOptions:
    """
    Helper class to easily provide the translation providers for a language for form fields.
    """

    language_tree_node: LanguageTreeNode

    @property
    def choices(self) -> list[tuple[str, str]]:
        """
        :attr:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode.mt_providers` as list of tuples for :attr:`django.forms.ChoiceField.choices`
        """
        return [
            (provider.name, provider.name)
            for provider in self.language_tree_node.mt_providers
        ]

    @property
    def providers(self) -> dict[str, MachineTranslationProviderType]:
        """
        :attr:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode.mt_providers` as a dict, indexed by :attr:`~integreat_cms.core.utils.machine_translation_provider.MachineTranslationProvider.name`
        """
        return {
            provider.name: provider for provider in self.language_tree_node.mt_providers
        }

    @property
    def initial(self) -> str:
        """
        :attr:`mt_provider.name <integreat_cms.core.utils.machine_translation_provider.MachineTranslationProvider.name>` for :attr:`django.forms.Field.initial`
        """
        return self.language_tree_node.mt_provider.name


class TranslationsManagementForm(CustomModelForm):
    """
    Form for modifying machine translation settings of a region
    """

    #: The languages that cannot be selected at the moment
    unavailable_languages: list[str] = []

    class Meta:
        """
        This class contains additional meta configuration of the form class,
        see the :class:`django.forms.ModelForm` for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Region
        #: The fields of the model which should be handled by this form
        fields = [
            "machine_translate_pages",
            "machine_translate_events",
            "machine_translate_pois",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize translations management form

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        """
        self.uncleaned_data: Any = kwargs.get("data")
        super().__init__(*args, **kwargs)
        self.languages_dict = kwargs.pop("languages_dict", {})
        languages = self.instance.language_tree_nodes.filter(
            active=True, parent__isnull=False
        ).select_related("language")
        self.unavailable_languages = []
        for language in languages:
            if language.mt_provider:
                self.languages_dict[language.slug] = TranslationLanguageOptions(
                    language_tree_node=language
                )
            else:
                self.unavailable_languages.append(language.translated_name)

    def get_language_fields(self) -> Iterator[forms.ChoiceField]:
        """
        Generator for a :class:`django.forms.ChoiceField` for each language with the available translation providers
        """
        for slug, language_options in self.languages_dict.items():
            self.fields[slug] = forms.ChoiceField(
                label=language_options.language_tree_node.translated_name,
                choices=language_options.choices,
                initial=language_options.initial,
            )
            yield self[slug]

    def save(self, commit: bool = True) -> Region:
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :return: The saved region object
        """
        # Save CustomModelForm
        region = super().save(commit=commit)

        # Iterate over all machine translatable languages and toggle them based on the checkbox value
        for lang, language_options in self.languages_dict.items():
            if provider_name := self.uncleaned_data.get(lang, None):
                if provider_name in language_options.providers:
                    language_options.language_tree_node.preferred_mt_provider = (
                        language_options.providers[provider_name]
                    )
                    language_options.language_tree_node.save()
                    logger.info(
                        "%s: Set provider %s for %s", region.slug, provider_name, lang
                    )
                else:
                    logger.info(
                        "%s: Bogus provider %r for %s! (acceptable values: %s)",
                        region.slug,
                        provider_name,
                        lang,
                        ", ".join(language_options.providers.keys()),
                    )
            else:
                logger.info(
                    "%s: Provider for language %s was not sent", region.slug, lang
                )

        return region
