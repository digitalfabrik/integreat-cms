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
    :type pages: ~django.db.models.query.QuerySet [ ~cms.models.pages.page.Page ]

    :return: The last root page of the given :class:`~django.db.models.query.QuerySet`
    :rtype: ~cms.models.pages.page.Page
    """
    return pages.filter(parent=None).last()


@register.filter
def get_descendants(page):
    """
    This filter returns the ids of all the page's descendants.

    :param page: The requested page
    :type page: ~cms.models.pages.page.Page

    :return: The list of all the page's descendants' ids
    :rtype: list [ int ]
    """
    return [descendant.id for descendant in page.get_descendants(include_self=True)]
