"""
This is a collection of tags and filters for :class:`~cms.models.pages.page.Page` objects.
"""
from django import template

register = template.Library()


@register.simple_tag
def get_last_root_page(pages):
    """
    This tag returns the last page on the root level.

    :param pages: The requested page tree
    :type pages: list [ ~cms.models.pages.page.Page ]

    :return: The last root page of the given page list
    :rtype: ~cms.models.pages.page.Page
    """
    root_pages = list(filter(lambda p: not p.parent, pages))
    return root_pages[-1] if root_pages else None


@register.simple_tag
def get_depth_in(node, pageset):
    """
    This tag returns the depth of node whithin the tree/pages in pageset.

    :param node : the page
    :type node : ~cms.models.pages.page.Page

    :param pageset: The pages (all pages or pages chosen by filter)
    :type pageset: list [ ~cms.models.pages.page.Page ]

    :return: the depth of node whithin the tree/pages in pageset
    :rtype: int
    """
    if not node.parent in pageset:
        return 0
    return node.depth - get_highest_anscentor_in(node, pageset).depth


def get_highest_anscentor_in(node, pageset):
    """
    This tag returns the highest (farthest) anscestor of node whithin the tree/pages in pageset.

    :param node : the page
    :type node : ~cms.models.pages.page.Page

    :param pageset: The pages (all pages or pages chosen by filter)
    :type pageset: list [ ~cms.models.pages.page.Page ]

    :return: the highest (farthest) anscestor of node whithin the tree/pages in pageset
    :rtype:  ~cms.models.pages.page.Page
    """
    if node.parent in pageset:
        return get_highest_anscentor_in(node.parent, pageset)
    return node
