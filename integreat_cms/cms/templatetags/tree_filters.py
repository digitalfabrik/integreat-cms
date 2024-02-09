"""
This is a collection of tags and filters for models which inherit from the MPTT model
:class:`~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode`
(:class:`~integreat_cms.cms.models.pages.page.Page` and
:class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from ..models import LanguageTreeNode, Page

register = template.Library()


@register.filter
def get_descendant_ids(node: LanguageTreeNode | Page) -> list[int]:
    """
    This filter returns the ids of all the node's descendants.

    :param node: The requested node
    :return: The list of all the node's descendants' ids
    """
    return [
        descendant.id for descendant in node.get_cached_descendants(include_self=True)
    ]


@register.filter
def get_children_ids(node: Page) -> list[int]:
    """
    This filter returns the ids of all the node's direct children.

    :param node: The requested node
    :return: The list of all the node's children's ids
    """
    return [child.id for child in node.cached_children]
