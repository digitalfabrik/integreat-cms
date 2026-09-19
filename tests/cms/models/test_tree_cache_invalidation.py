"""
Test that the cache is invalidated around all of treebeard's tree operations.

Treebeard shifts the ``lft``, ``rgt`` and ``tree_id`` of arbitrary other nodes with raw
``QuerySet.update()`` calls, which cacheops cannot see. If an operation does not invalidate the
model, a later request can read pre-shift coordinates from the cache and treebeard will then
insert a node at a position that no longer exists, silently writing the node into the wrong
branch. Cacheops is disabled in the test settings and needs a redis server, so these tests
assert that the invalidation happens instead of observing the cache itself.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from treebeard.ns_tree import NS_NodeManager

from integreat_cms.cms.models import (
    Language,
    LanguageTreeNode,
    Page,
    PageTranslation,
    Region,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from django.db.models import Model

#: Whether the tree operations are implemented on the manager, which is the case from
#: django-treebeard 7 on. Before that, they are implemented on the node itself.
TREE_OPERATIONS_ON_MANAGER = hasattr(NS_NodeManager, "add_child")

#: Skip the tests for the manager operations if this version of django-treebeard does not have them
requires_manager_operations = pytest.mark.skipif(
    not TREE_OPERATIONS_ON_MANAGER,
    reason="django-treebeard < 7 implements the tree operations on the node, not on the manager",
)


@contextmanager
def record_invalidated_models() -> Iterator[list[type[Model]]]:
    """
    Record which models would be invalidated instead of connecting to redis

    :return: The list the invalidated models are appended to
    """
    invalidated: list[type[Model]] = []
    with (
        patch(
            "integreat_cms.cms.models.abstract_tree_node.invalidate_model",
            invalidated.append,
        ),
        patch(
            "integreat_cms.cms.models.pages.page.invalidate_model",
            invalidated.append,
        ),
    ):
        yield invalidated


def create_page_tree() -> tuple[Page, Page, Page]:
    """
    Create a region with a root page and two children

    :return: The root page and both of its children
    """
    region = Region.objects.create(name="Testregion")
    root = Page.add_root(region=region)
    first_child = root.add_child(region=region)
    second_child = root.add_child(region=region)
    return root, first_child, second_child


def create_language_tree() -> tuple[LanguageTreeNode, LanguageTreeNode]:
    """
    Create a region with a root language tree node and one child

    :return: The root language tree node and its child
    """
    region = Region.objects.create(name="Testregion")
    languages = [
        Language.objects.create(
            slug=f"tl{index}",
            bcp47_tag=f"tl{index}",
            native_name=f"Testsprache {index}",
            english_name=f"Test language {index}",
            text_direction="ltr",
            primary_country_code="TEST",
            table_of_contents=f"Inhalt {index}",
        )
        for index in range(2)
    ]
    root = LanguageTreeNode.add_root(region=region, language=languages[0])
    child = root.add_child(region=region, language=languages[1])
    return root, child


@pytest.mark.django_db
def test_add_child_invalidates_cache() -> None:
    """
    Test whether adding a child page invalidates the cached pages and page translations
    """
    root, _first_child, _second_child = create_page_tree()
    with record_invalidated_models() as invalidated:
        root.add_child(region=root.region)
    assert Page in invalidated
    assert PageTranslation in invalidated


@pytest.mark.django_db
def test_add_sibling_invalidates_cache() -> None:
    """
    Test whether adding a sibling page invalidates the cached pages and page translations
    """
    _root, first_child, _second_child = create_page_tree()
    with record_invalidated_models() as invalidated:
        first_child.add_sibling(pos="right", region=first_child.region)
    assert Page in invalidated
    assert PageTranslation in invalidated


@pytest.mark.django_db
def test_move_invalidates_cache() -> None:
    """
    Test whether moving a page invalidates the cached pages and page translations
    """
    _root, first_child, second_child = create_page_tree()
    with record_invalidated_models() as invalidated:
        first_child.move(second_child, "right")
    assert Page in invalidated
    assert PageTranslation in invalidated


@pytest.mark.django_db
def test_delete_invalidates_cache() -> None:
    """
    Test whether deleting a page invalidates the cached pages and page translations, because
    closing the gap in the tree shifts the coordinates of all following nodes
    """
    _root, first_child, _second_child = create_page_tree()
    with record_invalidated_models() as invalidated:
        first_child.delete()
    assert Page in invalidated
    assert PageTranslation in invalidated


@pytest.mark.django_db
def test_queryset_delete_invalidates_cache() -> None:
    """
    Test whether deleting pages via the queryset invalidates the cached pages and page translations
    """
    _root, first_child, _second_child = create_page_tree()
    with record_invalidated_models() as invalidated:
        Page.objects.filter(pk=first_child.pk).delete()
    assert Page in invalidated
    assert PageTranslation in invalidated


@pytest.mark.django_db
def test_language_tree_node_delete_invalidates_cache() -> None:
    """
    Test whether deleting a language tree node invalidates the cached language tree nodes.
    This covers the shared manager and queryset instead of the ones overridden for pages.
    """
    _root, child = create_language_tree()
    with record_invalidated_models() as invalidated:
        child.delete()
    assert LanguageTreeNode in invalidated
    assert PageTranslation not in invalidated


@requires_manager_operations
@pytest.mark.django_db
def test_manager_add_child_invalidates_cache() -> None:
    """
    Test whether adding a child page via the manager invalidates the cache. This is the code path
    ``treebeard.forms.MoveNodeForm.save()`` takes, which is how pages are created in the CMS.
    """
    root, _first_child, _second_child = create_page_tree()
    with record_invalidated_models() as invalidated:
        Page.objects.add_child(root, create_kwargs={"region": root.region})
    assert Page in invalidated
    assert PageTranslation in invalidated


@requires_manager_operations
@pytest.mark.django_db
def test_manager_add_sibling_invalidates_cache() -> None:
    """
    Test whether adding a sibling page via the manager invalidates the cache
    """
    _root, first_child, _second_child = create_page_tree()
    with record_invalidated_models() as invalidated:
        Page.objects.add_sibling(
            first_child,
            pos="right",
            create_kwargs={"region": first_child.region},
        )
    assert Page in invalidated
    assert PageTranslation in invalidated


@requires_manager_operations
@pytest.mark.django_db
def test_manager_move_invalidates_cache() -> None:
    """
    Test whether moving a page via the manager invalidates the cache. This is the code path
    ``treebeard.forms.MoveNodeForm.save()`` and ``treebeard.admin.TreeAdmin.move_node()`` take.
    """
    _root, first_child, second_child = create_page_tree()
    with record_invalidated_models() as invalidated:
        Page.objects.move(first_child, second_child, pos="right")
    assert Page in invalidated
    assert PageTranslation in invalidated
