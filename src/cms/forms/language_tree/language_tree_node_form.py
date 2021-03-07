import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from ..custom_model_form import CustomModelForm
from ...models import Language, LanguageTreeNode


logger = logging.getLogger(__name__)


class LanguageField(forms.ModelChoiceField):
    """
    Form field helper class to overwrite the label function (which would otherwise call __str__)
    """

    def label_from_instance(self, obj):
        return obj.translated_name


class LanguageTreeNodeForm(CustomModelForm):
    """
    Form for creating and modifying language tree node objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = LanguageTreeNode
        #: The fields of the model which should be handled by this form
        fields = ["language", "parent", "visible", "active"]
        #: The custom field classes to be used in this form
        field_classes = {
            "language": LanguageField,
            "parent": LanguageField,
        }

    def __init__(self, *args, **kwargs):
        logger.info(
            "LanguageTreeNodeForm instantiated with data %s and instance %s",
            kwargs.get("data"),
            kwargs.get("instance"),
        )

        # current region
        region = kwargs.pop("region", None)

        super().__init__(*args, **kwargs)

        parent_queryset = region.language_tree_nodes
        excluded_languages = region.languages.exclude(language_tree_nodes=self.instance)

        if self.instance.id:
            children = self.instance.get_descendants(include_self=True)
            parent_queryset = parent_queryset.exclude(id__in=children)
        else:
            self.instance.region = region

        # limit possible parents to nodes of current region
        self.fields["parent"].queryset = parent_queryset
        # limit possible languages to those which are not yet included in the tree
        self.fields["language"].queryset = Language.objects.exclude(
            id__in=excluded_languages
        )

    def save(self, commit=True):
        """
        Function to save the form instance

        :return: The saved language tree node object
        :rtype: ~cms.models.languages.language_tree_node.LanguageTreeNode
        """
        logger.info(
            "LanguageTreeNodeForm saved with cleaned data %s and changed data %s",
            self.cleaned_data,
            self.changed_data,
        )

        return super().save(commit=commit)

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`:
        Don't allow multiple root nodes for one region:
        If self is a root node and the region already has a default language, raise a
        :class:`~django.core.exceptions.ValidationError`.

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()
        logger.info("LanguageTreeNodeForm cleaned with cleaned data %s", cleaned_data)
        default_language = self.instance.region.default_language
        # There are two cases in which this error is thrown.
        # Both cases include that the parent field is None.
        # 1. The instance does exist:
        #   - The default language is different from the instance language
        # 2. The instance does not exist:
        #   - The default language exists
        if not cleaned_data.get("parent") and (
            (self.instance.id and default_language != self.instance.language)
            or (not self.instance.id and default_language)
        ):
            self.add_error(
                "parent",
                forms.ValidationError(
                    _(
                        "This region has already a default language."
                        "Please specify a source language for this language."
                    ),
                    code="invalid",
                ),
            )
        return cleaned_data
