"""
We use `django-rules <https://pypi.org/project/rules/>`_ to add custom permissions for specific pages.

For a given user and page, the following permissions are added:

* ``~integreat_cms.cms.edit_page`` if one of the following predicates return true:

    * :func:`~integreat_cms.cms.rules.can_edit_all_pages`
    * :func:`~integreat_cms.cms.rules.is_page_author`
    * :func:`~integreat_cms.cms.rules.can_publish_all_pages`
    * :func:`~integreat_cms.cms.rules.is_page_editor`

* ``~integreat_cms.cms.publish_page_object`` if one of the following predicates return true:

    * :func:`~integreat_cms.cms.rules.can_publish_all_pages`
    * :func:`~integreat_cms.cms.rules.is_page_editor`

See the project's `README <https://github.com/dfunckt/django-rules/blob/master/README.rst>`_ to learn more.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rules import add_perm, predicate

if TYPE_CHECKING:
    from .models import ChatMessage, Page, User

# Predicates


@predicate
def is_page_author(user: User, page: Page | None) -> bool:
    """
    This predicate checks whether the given user is one of the authors of the given page.

    :param user: The user who's permission should be checked
    :param page: The requested page
    :return: Whether or not ``user`` is an author of ``page``
    """
    if not page or not page.id:
        return False
    return user in page.authors.all()


@predicate
def is_page_editor(user: User, page: Page | None) -> bool:
    """
    This predicate checks whether the given user is one of the editors of the given page.

    :param user: The user who's permission should be checked
    :param page: The requested page
    :return: Whether or not ``user`` is an editor of ``page``
    """
    if not page or not page.id:
        return False
    return user in page.editors.all()


@predicate
def can_edit_all_pages(user: User, page: Page | None) -> bool:
    """
    This predicate checks whether the given user can edit all pages.

    :param user: The user who's permission should be checked
    :param page: The page parameter is used for the region check
    :return: Whether or not ``user`` can edit all pages
    """
    if (
        not user.is_superuser
        and not user.is_staff
        and page
        and page.id
        and page.region not in user.regions.all()
    ):
        return False
    return user.has_perm("cms.change_page")


@predicate
def can_publish_all_pages(user: User, page: Page | None) -> bool:
    """
    This predicate checks whether the given user can publish all pages.

    :param user: The user who's permission should be checked
    :param page: The page parameter is used for the region check
    :return: Whether or not ``user`` can publish all pages
    """
    if not (user.is_superuser or user.is_staff):
        if page and page.id and page.region not in user.regions.all():
            return False
    return user.has_perm("cms.publish_page")


@predicate
def is_in_responsible_organization(user: User, page: Page | None) -> bool:
    """
    This predicate checks whether the given user is a member of the page's responsible organization.

    :param user: The user who's permission should be checked
    :param page: The requested page
    :return: Whether or not ``user`` is a member of ``page.organization``
    """
    if not page or not page.id or not page.organization:
        return False
    return user in page.organization.members.all()


@predicate
def can_delete_chat_message(user: User, chat_message: ChatMessage) -> bool:
    """
    This predicate checks whether the given user can delete a given chat message

    :param user: The user who's permission should be checked
    :param chat_message: The requested chat message
    :return: Whether or not ``user`` is allowed to delete ``chat_message``
    """
    # Check if user has the permission to delete all chat messages
    if user.has_perm("cms.delete_chat_message"):
        return True
    # Normal users can only delete their own messages
    return user == chat_message.sender


# Permissions

add_perm(
    "cms.change_page_object",
    can_edit_all_pages
    | is_page_author
    | can_publish_all_pages
    | is_page_editor
    | is_in_responsible_organization,
)
add_perm(
    "cms.publish_page_object",
    can_publish_all_pages | is_page_editor | is_in_responsible_organization,
)
add_perm("cms.delete_chat_message_object", can_delete_chat_message)
