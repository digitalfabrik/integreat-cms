import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from ...models import Language, LanguageTreeNode


logger = logging.getLogger(__name__)


class LanguageField(forms.ModelChoiceField):
    """
    Form field helper class to overwrite the label function (which would otherwise call __str__)
    """

    def label_from_instance(self, obj):
        return obj.translated_name


class LanguageTreeNodeForm(forms.ModelForm):
    """
    Form for creating and modifying language tree node objects
    """

    class Meta:
        model = LanguageTreeNode
        fields = ["language", "parent", "active"]
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
            parent_queryset = parent_queryset.difference(children)
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
        Function to create or update a language tree node
        """
        logger.info(
            "LanguageTreeNodeForm saved with cleaned data %s and changed data %s",
            self.cleaned_data,
            self.changed_data,
        )

        return super().save(commit=commit)

    def clean(self):
        """
        Don't allow multiple root nodes for one region:
            If self is a root node and the region already has a default language,
            raise a validation error.
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
