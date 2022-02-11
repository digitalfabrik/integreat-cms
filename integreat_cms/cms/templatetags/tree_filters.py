"""
This is a collection of tags and filters for models which inherit from the MPTT model
:class:`~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode`
(:class:`~integreat_cms.cms.models.pages.page.Page` and
:class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode`).
"""
from django import template

register = template.Library()


@register.filter
def get_descendant_ids(node):
    """
    This filter returns the ids of all the node's descendants.

    :param node: The requested node
    :type node: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode

    :return: The list of all the node's descendants' ids
    :rtype: list [ int ]
    """
    return [
        descendant.id for descendant in node.get_cached_descendants(include_self=True)
    ]


@register.filter
def get_children_ids(node):
    """
    This filter returns the ids of all the node's direct children.

    :param node: The requested node
    :type node: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode

    :return: The list of all the node's children's ids
    :rtype: list [ int ]
    """
    return [child.id for child in node.cached_children]
