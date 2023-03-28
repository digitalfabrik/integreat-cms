import logging

from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from ...models import Language, LanguageTreeNode
from ...utils.translation_utils import mt_to_lang_is_permitted

logger = logging.getLogger(__name__)


class MachineTranslationForm(forms.Form):
    """
    Form for selecting target languages for machine translation of a content object.
    """

    automatic_translation = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        label=_("Automatic translation"),
        help_text=_(
            "Tick if updating this content should automatically refresh or create its translations."
        ),
    )

    translations_to_update = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        queryset=LanguageTreeNode.objects.none(),
        required=False,
        label=_("Update existing translations:"),
    )

    translations_to_create = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        queryset=LanguageTreeNode.objects.none(),
        required=False,
        label=_("Create new translations:"),
    )

    def __init__(self, instance, region, language, **kwargs):
        r"""
        Initialize MT translation form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        super().__init__(**kwargs)

        parent_node = region.language_node_by_slug.get(language.slug)
        translation_targets = [
            language_node
            for language_node in region.language_tree
            if language_node.active
            and language_node.parent_id
            and language_node.parent_id == parent_node.id
            and language_node.mt_provider
            and mt_to_lang_is_permitted(region, language_node.slug)
        ]

        # completely hide options if no target languages exist
        if not translation_targets:
            del self.fields["automatic_translation"]
            return

        # if this translation exists, use its saved automatic_translation setting
        try:
            self.initial["automatic_translation"] = instance.get_translation(
                language.slug
            ).automatic_translation
        except AttributeError:
            pass

        to_update, to_create = [], []
        for target in translation_targets:
            target_type = (
                to_update
                if instance and instance.get_translation(target.slug)
                else to_create
            )
            target_type.append(target.id)

        self.fields[
            "translations_to_update"
        ].queryset = region.language_tree_nodes.filter(id__in=to_update)
        self.fields[
            "translations_to_create"
        ].queryset = region.language_tree_nodes.filter(id__in=to_create)

        self.initial["translations_to_update"] = to_update

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        if not cleaned_data.get("automatic_translation"):
            cleaned_data["translations_to_update"] = LanguageTreeNode.objects.none()
            cleaned_data["translations_to_create"] = LanguageTreeNode.objects.none()
        return cleaned_data

    def get_target_languages(self):
        """
        Return all selected target languages

        :return: The target language slugs
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.languages.language.Language ]
        """
        return Language.objects.filter(
            Q(language_tree_nodes__in=self.cleaned_data.get("translations_to_update"))
            | Q(
                language_tree_nodes__in=self.cleaned_data.get("translations_to_create")
            ),
        )
