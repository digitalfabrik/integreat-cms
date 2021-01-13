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
    return list(filter(lambda p: not p.parent, pages))[-1]
