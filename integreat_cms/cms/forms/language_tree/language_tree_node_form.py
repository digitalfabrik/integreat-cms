import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from cacheops import invalidate_obj

from ...constants import position
from ...models import Language, LanguageTreeNode
from ..custom_model_form import CustomModelForm
from ..custom_tree_node_form import CustomTreeNodeForm


logger = logging.getLogger(__name__)


class LanguageTreeNodeForm(CustomModelForm, CustomTreeNodeForm):
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
        fields = ["language", "visible", "active", "parent"]

    def __init__(self, **kwargs):
        r"""
        Initialize language tree node form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """

        # Instantiate CustomModelForm and CustomTreeNodeForm
        super().__init__(**kwargs)

        # Make position field optional because we're overriding that value anyway
        self.fields["_position"].required = False

        parent_queryset = self.instance.region.language_tree_nodes

        if self.instance.id:
            descendant_ids = [
                descendant.id
                for descendant in self.instance.get_cached_descendants(
                    include_self=True
                )
            ]
            parent_queryset = parent_queryset.exclude(id__in=descendant_ids)
            excluded_languages = [
                language.id
                for language in self.instance.region.languages
                if language != self.instance.language
            ]
        else:
            # Make sure it's not possible to create multiple nodes for the same language
            excluded_languages = [
                language.id for language in self.instance.region.languages
            ]

        # limit possible parents to nodes of current region
        self.fields["parent"].queryset = parent_queryset
        self.fields["_ref_node_id"].choices = self.fields["parent"].choices
        # limit possible languages to those which are not yet included in the tree
        self.fields["language"].queryset = Language.objects.exclude(
            id__in=excluded_languages
        )

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

        # Ignore the value that is submitted as ref node and just use the parent field
        parent = cleaned_data.get("parent")
        cleaned_data["_ref_node_id"] = str(parent.id) if parent else ""
        cleaned_data["_position"] = position.FIRST_CHILD

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
        logger.debug(
            "LanguageTreeNodeForm validated [2] with cleaned data %r", cleaned_data
        )
        return cleaned_data

    def save(self, commit=True):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to flush
        the cache after committing.

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :return: The saved page translation object
        :rtype: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """
        # Save CustomModelForm and CustomTreeNodeForm
        result = super().save(commit=commit)

        # Flush cache of content objects
        for page in self.instance.region.pages.all():
            invalidate_obj(page)
        for poi in self.instance.region.pois.all():
            invalidate_obj(poi)
        for event in self.instance.region.events.all():
            invalidate_obj(event)
        return result
