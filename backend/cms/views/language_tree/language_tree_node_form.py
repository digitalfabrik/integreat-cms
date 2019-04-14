"""
Form for creating a language tree node object
"""

from django import forms
from ...models import LanguageTreeNode, Site
from ..general import POSITION_CHOICES


class LanguageTreeNodeForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    position = forms.ChoiceField(choices=POSITION_CHOICES)

    class Meta:
        model = LanguageTreeNode
        fields = ['language', 'parent', 'active']


    def __init__(self, *args, **kwargs):
        super(LanguageTreeNodeForm, self).__init__(*args, **kwargs)

    def save_page(self, site_slug, language_tree_node_id=None):
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
                site=Site.objects.get(slug=site_slug),
                active=self.cleaned_data['active'],
                parent=self.cleaned_data['parent'],
            )
