"""
We use `django-rules <https://pypi.org/project/rules/>`_ to add custom permissions for specific pages.

For a given user and page, the following permissions are added:

* ``cms.edit_page`` if one of the following predicates return true:

    * :func:`~cms.rules.can_edit_all_pages`
    * :func:`~cms.rules.is_page_editor`
    * :func:`~cms.rules.can_publish_all_pages`
    * :func:`~cms.rules.is_page_publisher`

* ``cms.publish_page`` if one of the following predicates return true:

    * :func:`~cms.rules.can_publish_all_pages`
    * :func:`~cms.rules.is_page_publisher`

See the project's `README <https://github.com/dfunckt/django-rules/blob/master/README.rst>`_ to learn more.
"""
from rules import add_perm, predicate


# Predicates

@predicate
def is_page_editor(user, page):
    """
    This predicate checks whether the given user is one of the editors of the given page.

    :param user: The user who's permission should be checked
    :type user: ~django.contrib.auth.models.User

    :param page: The requested page
    :type page: ~cms.models.pages.page.Page

    :return: Whether or not ``user`` is an editor of ``page``
    :rtype: bool
    """
    if not page:
        return False
    return user in page.editors.all()

@predicate
def is_page_publisher(user, page):
    """
    This predicate checks whether the given user is one of the publishers of the given page.

    :param user: The user who's permission should be checked
    :type user: ~django.contrib.auth.models.User

    :param page: The requested page
    :type page: ~cms.models.pages.page.Page

    :return: Whether or not ``user`` is a publisher of ``page``
    :rtype: bool
    """
    if not page:
        return False
    return user in page.publishers.all()

@predicate
# pylint: disable=unused-argument
def can_edit_all_pages(user, page):
    """
    This predicate checks whether the given user can edit all pages.

    :param user: The user who's permission should be checked
    :type user: ~django.contrib.auth.models.User

    :param page: Unused page parameter (the function signature must match the other predicates)
    :type page: ~cms.models.pages.page.Page

    :return: Whether or not ``user`` can edit all pages
    :rtype: bool
    """
    return user.has_perm('cms.edit_pages')

@predicate
# pylint: disable=unused-argument
def can_publish_all_pages(user, page):
    """
    This predicate checks whether the given user can publish all pages.

    :param user: The user who's permission should be checked
    :type user: ~django.contrib.auth.models.User

    :param page: Unused page parameter (the function signature must match the other predicates)
    :type page: ~cms.models.pages.page.Page

    :return: Whether or not ``user`` can publish all pages
    :rtype: bool
    """
    return user.has_perm('cms.publish_pages')


# Permissions

add_perm('cms.edit_page', can_edit_all_pages | is_page_editor | can_publish_all_pages | is_page_publisher)
add_perm('cms.publish_page', can_publish_all_pages | is_page_publisher)
