"""
Form for creating a language tree node object
"""

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django import forms
from ...models import LanguageTreeNode, Region


class LanguageTreeNodeForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = LanguageTreeNode
        fields = ['language', 'parent', 'active']


    def __init__(self, *args, **kwargs):
        region_slug = kwargs.pop('region_slug', None)
        if region_slug:
            self.region = Region.objects.get(slug=region_slug)
        super(LanguageTreeNodeForm, self).__init__(*args, **kwargs)

    def save_language_node(self, language_tree_node_id=None):
        """Function to create or update a page
            language_tree_node_id ([Integer], optional): Defaults to None. If it's not set creates
            a language tree node or update the language tree node with the given page id.
        """

        # TODO: version, active_version
        if language_tree_node_id:
            # save language tree node
            language_tree_node = LanguageTreeNode.objects.get(id=language_tree_node_id)
            language_tree_node.language = self.cleaned_data['language']
            language_tree_node.active = self.cleaned_data['active']
            language_tree_node.parent = self.cleaned_data['parent']
            language_tree_node.save()
        else:
            # create language tree node
            language_tree_node = LanguageTreeNode.objects.create(
                language=self.cleaned_data['language'],
                region=self.region,
                active=self.cleaned_data['active'],
                parent=self.cleaned_data['parent'],
            )

        return language_tree_node

    def clean(self):
        """
        Don't allow multiple root nodes for one region:
            If self is a root node and the region already has a default language,
            raise a validation error.
        """
        if not self.cleaned_data['parent'] and self.region.default_language:
            raise ValidationError(_('This region has already a default language.'
                                    'Please specify a source language for this language.'))
        #    Require all nodes of one tree to have the same region:
        #    If self has a parent node, check if the parent's region equals the region of self.
        if (
                self.cleaned_data['parent']
                and
                self.cleaned_data['parent'].region != self.region
        ):
            raise ValidationError(_('The source language belongs to another region.'
                                    'Please specify a source language of this region.'))
