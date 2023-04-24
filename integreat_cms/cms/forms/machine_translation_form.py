import logging

from django import forms
from django.utils.translation import gettext_lazy as _

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
        widget=forms.CheckboxSelectMultiple(),
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

    def __init__(self, **kwargs):
        r"""
        Initialize MT translation form. If request and language kwargs are missing, MTs are disabled.

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
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

        to_update, to_create = [], []
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

    def mt_form_is_enabled(self):
        """
        Helper method to decide if this form should be shown, or if it should be hidden for
        the current language due to a lack of MT-compatible child language nodes

        :return: Whether this form is enabled
        :rtype: bool
        """
        return (
            self.fields["mt_translations_to_update"].queryset
            or self.fields["mt_translations_to_create"].queryset
        )

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        if not cleaned_data.get("automatic_translation"):
            cleaned_data["mt_translations_to_create"] = LanguageTreeNode.objects.none()
            cleaned_data["mt_translations_to_update"] = LanguageTreeNode.objects.none()
        return cleaned_data

    def save(self, commit=True, foreign_form_changed=False):
        """
        Create machine translations and save them to the database

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :param foreign_form_changed: Whether or not the foreign form of this translation form was changed
        :type foreign_form_changed: bool

        :return: The saved content translation object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
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
