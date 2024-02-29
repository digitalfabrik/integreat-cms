"""
This is a collection of tags and filters for :class:`~integreat_cms.cms.models.pages.page.Page` objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from ..models import Page
    from ..models.pages.page import PageQuerySet

register = template.Library()


@register.simple_tag
def get_depth_in(node: Page, pageset: PageQuerySet) -> int:
    """
    This tag returns the depth of node within the tree/pages in pageset.

    :param node : the page
    :param pageset: The pages (all pages or pages chosen by filter)
    :return: the depth of node within the tree/pages in pageset
    """
    if node.parent not in pageset:
        return 0
    return node.depth - get_highest_anscentor_in(node, pageset).depth


def get_highest_anscentor_in(node: Page, pageset: PageQuerySet) -> Page:
    """
    This tag returns the highest (farthest) ancestor of node within the tree/pages in pageset.

    :param node : the page
    :param pageset: The pages (all pages or pages chosen by filter)
    :return: the highest (farthest) ancestor of node within the tree/pages in pageset
    """
    if node.parent in pageset:
        return get_highest_anscentor_in(node.parent, pageset)
    return node
