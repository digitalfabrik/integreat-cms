import json

"""
This is a collection of tags and filters for models which inherit from the MPTT model
(:class:`~integreat_cms.cms.models.pages.page.Page` and :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode`).
"""
from django import template

register = template.Library()


@register.filter
def get_descendants(node):
    """
    This filter returns the ids of all the node's descendants.

    :param node: The requested node
    :type node: ~integreat_cms.cms.models.pages.page.Page or ~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode

    :return: The list of all the node's descendants' ids
    :rtype: list [ int ]
    """
    return get_descendants_recursive(node)


@register.filter
def get_translation_state(node, language_id):
    return node["translation_state"][str(language_id)] or "missing"


def get_descendants_recursive(node):
    descendants = [child["page_id"] for child in node["children"]]
    for child in node["children"]:
        descendants += get_descendants_recursive(child)
    return descendants


@register.filter
def get_children(node):
    """
    This filter returns the ids of all the node's direct children.

    :param node: The requested node
    :type node: ~integreat_cms.cms.models.pages.page.Page or ~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode

    :return: The list of all the node's children's ids
    :rtype: list [ int ]
    """
    return [child["page_id"] for child in node["children"]]
