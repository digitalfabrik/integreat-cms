from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Any

    from treebeard.ns_tree import NS_NodeQuerySet

    from ..models import EventTranslation, PageTranslation, POITranslation

from ...core.utils.machine_translation_provider import MachineTranslationProvider
from ...textlab_api.utils import check_hix_score
from ..models import LanguageTreeNode
from .custom_content_model_form import CustomContentModelForm

logger = logging.getLogger(__name__)


class MachineTranslationForm(CustomContentModelForm):
    """
    Form for selecting target languages for machine translation of a content object.
    It should be used as base class for translation forms which enable machine translations.
    """

    mt_translations_to_create = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "bulk-select-language", "name": "selected_language_slugs[]"}
        ),
        queryset=LanguageTreeNode.objects.none(),
        required=False,
        label=_("Create new translations:"),
    )

    mt_translations_to_update = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        queryset=LanguageTreeNode.objects.none(),
        required=False,
        label=_("Update existing translations:"),
    )

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize MT translation form. If request and language kwargs are missing, MTs are disabled.

        :param \**kwargs: The supplied keyword arguments
        """
        # Pop kwargs to make sure the super class does not get this params
        self.request = kwargs.pop("request", None)
        self.language = kwargs.pop("language", None)

        # Initialize CustomContentModelForm
        super().__init__(**kwargs)

        if not self.request or not self.language:
            self.logger.debug(
                "%s initialized without support for machine translations",
                type(self).__name__,
            )
            return

        if not MachineTranslationProvider.is_permitted(
            self.request.region, self.request.user, self._meta.model
        ):
            return

        parent_node = self.request.region.language_node_by_slug.get(self.language.slug)
        translation_targets = [
            language_node
            for language_node in self.request.region.language_tree
            if language_node.parent_id == parent_node.id and language_node.mt_provider
        ]

        to_create: list[int] = []
        to_update: list[int] = []
        for target in translation_targets:
            target_type = (
                to_update
                if self.instance.id
                and target.language in self.instance.foreign_object.languages
                else to_create
            )
            target_type.append(target.id)

        self.fields["mt_translations_to_create"].queryset = (
            self.request.region.language_tree_nodes.filter(id__in=to_create)
        )
        self.fields["mt_translations_to_update"].queryset = (
            self.request.region.language_tree_nodes.filter(id__in=to_update)
        )
        self.initial["mt_translations_to_update"] = to_update

    def mt_form_is_enabled(self) -> NS_NodeQuerySet:
        """
        Helper method to decide if this form should be shown, or if it should be hidden for
        the current language due to a lack of MT-compatible child language nodes

        :return: Whether this form is enabled
        """
        return (
            self.fields["mt_translations_to_update"].queryset
            or self.fields["mt_translations_to_create"].queryset
        )

    def clean(self) -> dict[str, Any]:
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        """
        cleaned_data = super().clean()

        if not cleaned_data.get("automatic_translation"):
            cleaned_data["mt_translations_to_create"] = LanguageTreeNode.objects.none()
            cleaned_data["mt_translations_to_update"] = LanguageTreeNode.objects.none()
        return cleaned_data

    def save(
        self, commit: bool = True, foreign_form_changed: bool = False
    ) -> EventTranslation | (PageTranslation | POITranslation):
        """
        Create machine translations and save them to the database

        :param commit: Whether or not the changes should be written to the database
        :param foreign_form_changed: Whether or not the foreign form of this translation form was changed
        :return: The saved content translation object
        """
        self.instance = super().save(commit, foreign_form_changed)

        language_nodes = self.cleaned_data["mt_translations_to_create"].union(
            self.cleaned_data["mt_translations_to_update"]
        )
        if commit and language_nodes and check_hix_score(self.request, self.instance):
            for language_node in language_nodes:
                logger.debug(
                    "Machine translation via %r into %r for: %r",
                    language_node.mt_provider,
                    language_node.language,
                    self.instance,
                )
                api_client = language_node.mt_provider.api_client(
                    self.request, type(self)
                )
                # Invalidate cached property to take new version into account
                self.instance.foreign_object.invalidate_cached_translations()
                api_client.translate_object(
                    self.instance.foreign_object, language_node.slug
                )
        return self.instance

    class Meta(CustomContentModelForm.Meta):
        """
        Inherit the meta class from the custom content model form
        """
