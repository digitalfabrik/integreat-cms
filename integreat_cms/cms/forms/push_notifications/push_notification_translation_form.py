from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from ....core.utils.machine_translation_provider import MachineTranslationProvider
from ...constants import push_notifications, text_directions
from ...models import LanguageTreeNode, PushNotificationTranslation
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest
    from treebeard.ns_tree import NS_NodeQuerySet

logger = logging.getLogger(__name__)


class PushNotificationTranslationForm(CustomModelForm):
    """
    Form for creating and modifying push notification translation objects
    """

    mt_translations_to_create = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "bulk-select-language",
                "name": "selected_language_slugs[]",
            },
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
            self.request.region,
            self.request.user,
            self._meta.model,
        ):
            return

        self.initial["automatic_translation"] = False

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

        self.fields[
            "mt_translations_to_create"
        ].queryset = self.request.region.language_tree_nodes.filter(id__in=to_create)
        self.fields[
            "mt_translations_to_update"
        ].queryset = self.request.region.language_tree_nodes.filter(id__in=to_update)
        self.initial["mt_translations_to_update"] = to_update

        localized_fields = ["title", "text"]
        for field in localized_fields:
            self.fields[field].widget.attrs["dir"] = (
                "rtl"
                if self.language.text_direction == text_directions.RIGHT_TO_LEFT
                else "ltr"
            )

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

        if not self.errors:
            self.instance.is_validated = True
        return cleaned_data

    def add_error_messages(self, request: HttpRequest) -> None:
        """
        This function overwrites :meth:`~integreat_cms.cms.forms.custom_model_form.CustomModelForm.add_error_messages`
        to add the language of the current translation to the error messages

        :param request: The current request submitting the form
        """
        # Add field errors
        for field in self:
            for error in field.errors:
                messages.error(
                    request,
                    f"{_(field.label)} ({self.instance.language.translated_name}): {_(error)}",
                )
        # Add non-field errors
        for error in self.non_field_errors():
            messages.error(
                request,
                f"{self.instance.language.translated_name}: {_(error)}",
            )
        # Add debug logging in english
        with override("en"):
            logger.debug(
                "PushNotificationTranslationForm submitted with errors: %r",
                self.errors,
            )

    def has_changed(self) -> bool:
        """
        Return ``True`` if submitted data differs from initial data.
        If the main language should be used as fallback for missing translations, this always return ``True``.

        :return: Whether the form has changed
        """
        if (
            hasattr(self.instance, "push_notification")
            and self.instance.push_notification.mode
            == push_notifications.USE_MAIN_LANGUAGE
        ):
            return True
        return super().has_changed()

    def save(
        self,
        commit: bool = True,
    ) -> PushNotificationTranslation:
        """
        Create machine translations and save them to the database

        :param commit: Whether or not the changes should be written to the database
        :return: The saved content translation object
        """
        self.instance = super().save()

        language_nodes = self.cleaned_data["mt_translations_to_create"].union(
            self.cleaned_data["mt_translations_to_update"],
        )
        if commit and language_nodes:
            for language_node in language_nodes:
                logger.debug(
                    "Machine translation via %r into %r for: %r",
                    language_node.mt_provider,
                    language_node.language,
                    self.instance,
                )
                api_client = language_node.mt_provider.api_client(
                    self.request,
                    type(self),
                )
                api_client.translate_object(
                    self.instance.foreign_object,
                    language_node.slug,
                )
        return self.instance

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = PushNotificationTranslation
        #: The fields of the model which should be handled by this form
        fields: list[str] = ["title", "text", "automatic_translation"]
