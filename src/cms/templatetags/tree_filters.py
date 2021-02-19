"""
This is a collection of tags and filters for models which inherit from the MPTT model
(:class:`~cms.models.pages.page.Page` and :class:`~cms.models.languages.language_tree_node.LanguageTreeNode`).
"""
from django import template

register = template.Library()


@register.filter
def get_descendants(node):
    """
    This filter returns the ids of all the node's descendants.

    :param node: The requested node
    :type node: ~cms.models.pages.page.Page or ~cms.models.languages.language_tree_node.LanguageTreeNode

    :return: The list of all the node's descendants' ids
    :rtype: list [ int ]
    """
    return [descendant.id for descendant in node.get_descendants(include_self=True)]


@register.filter
def get_children(node):
    """
    This filter returns the ids of all the node's direct children.

    :param node: The requested node
    :type node: ~cms.models.pages.page.Page or ~cms.models.languages.language_tree_node.LanguageTreeNode

    :return: The list of all the node's children's ids
    :rtype: list [ int ]
    """
    return [child.id for child in node.children.all()]
