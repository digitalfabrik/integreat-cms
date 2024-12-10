"""
This module contains utilities to repair or detect inconsistencies in a tree
"""

from __future__ import annotations

import logging
from collections import deque
from typing import TYPE_CHECKING

from django.apps import apps

from .shadow_instance import ShadowInstance
from .tree_mutex import tree_mutex

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.apps.registry import Apps
    from django.db.models import Model

    Page: Model = apps.get_model("cms", "Page")


@tree_mutex("page")
def repair_tree(
    page_id: Iterable[int] | None = None,
    commit: bool = False,
    logging_name: str = __name__,
    dj_apps: Apps = apps,
) -> None:
    """
    Fix the tree for a given page, or all trees if no id is given.
    Changes are only written to the database if ``commit`` is set to ``True``.
    For details see :class:`MPTTFixer`.
    """
    logger = logging.getLogger(logging_name)

    # Use get_model() instead of importing so this function can be used in migrations
    Page: Model = dj_apps.get_model("cms", "Page")
    mptt_fixer = MPTTFixer(dj_apps=dj_apps)
    root_nodes: Iterable[ShadowInstance[Page]]

    if page_id:
        # Assert that any of the requested pages actually exist
        for single_id in page_id:
            try:
                Page.objects.get(id=single_id)
            except Page.DoesNotExist as e:
                raise ValueError(
                    f'The page with id "{single_id}" does not exist.',
                ) from e
        # All ids in page_id are valid, get them from mptt_fixer
        root_nodes = {
            mptt_fixer.get_fixed_root_node(single_id) for single_id in page_id
        }
    else:
        root_nodes = mptt_fixer.get_fixed_root_nodes()

    for root_node in root_nodes:
        action = "Fixing" if commit else "Detecting problems in"
        logger.info(
            "%s tree with id %i... (%r)",
            action,
            root_node.tree_id__original,
            root_node.instance,
        )
        for tree_node in mptt_fixer.get_fixed_tree_of_page(root_node.pk):
            print_changed_fields(tree_node, logging_name=logging_name)

    if commit:
        for page in mptt_fixer.get_fixed_tree_nodes():
            page.apply_changes()
            page.save()


def print_changed_fields(
    tree_node: ShadowInstance[Page],
    logging_name: str = __name__,
) -> None:
    """
    Utility function to print changed and unchanged attributes using a
    :class:`~integreat_cms.cms.utils.shadow_instance.ShadowInstance` of the :class:`~integreat_cms.cms.models.pages.page.Page`.
    """
    logger = logging.getLogger(logging_name)

    diff = tree_node.changed_attributes

    logger.info("Page %s:", tree_node.id)
    logger.success("\tparent_id: %s", tree_node.parent_id)  # type: ignore[attr-defined]

    for name in ["tree_id", "depth", "lft", "rgt"]:
        if name in diff:
            logger.error("\t%s: %i → %i", name, diff[name]["old"], diff[name]["new"])
        else:
            logger.success("\t%s: %i", name, getattr(tree_node, name))  # type: ignore[attr-defined]


class MPTTFixer:
    """
    Gets ALL nodes and coughs out fixed ``lft``, ``rgt`` and ``depth`` values.
    Uses the parent field to fix hierarchy and sorts siblings by (potentially inconsistent) ``lft``.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, dj_apps: Apps = apps) -> None:
        """
        Create a fixed tree, using a :class:`~integreat_cms.cms.utils.shadow_instance.ShadowInstance` of each page.
        """
        Page: Model = dj_apps.get_model("cms", "Page")
        self.broken_nodes: deque[ShadowInstance[Page]] = deque(
            ShadowInstance(page) for page in Page.objects.all()
        )
        # A list of root nodes, also determining the new tree_id (index + 1)
        self.trees: list[ShadowInstance[Page]] = []
        # A dictionary of fixed nodes, indexable by primary key
        self.fixed_nodes: dict[int, ShadowInstance[Page]] = {}
        self.recreate_structure()
        self.fix_values()

    def recreate_structure(self) -> None:
        """
        Extract nodes and recreate their hierarchy.
        """
        while self.broken_nodes:
            node = self.broken_nodes.popleft()
            if node.parent_id is None:
                # This is a root node
                self.trees.append(node)
                node.tree_id = len(self.trees)
                node.depth = 1
            elif node.parent_id not in self.fixed_nodes:
                # We don't know the parent yet, put it back in the queue
                self.broken_nodes.append(node)
                continue
            else:
                # Adopt the tree id of the parent and register us as found child
                parent = self.fixed_nodes[node.parent_id]
                node.tree_id = parent.tree_id
                self.fixed_nodes[parent.pk].fixed_children.append(node.pk)
            # This node will have a list of which children have been found
            node.fixed_children = []
            self.fixed_nodes[node.pk] = node

    def get_fixed_root_nodes(self) -> Iterable[ShadowInstance[Page]]:
        """
        Yield all fixed root nodes.
        """
        return tuple(self.trees)

    def get_fixed_root_node(self, page_id: int) -> ShadowInstance[Page]:
        """
        Travel up ancestors of a page until we get the root node.
        """
        page = self.fixed_nodes[page_id]
        while page.parent_id is not None:
            page = self.fixed_nodes[page.parent_id]
        return page

    def get_fixed_tree_nodes(self) -> Iterable[ShadowInstance[Page]]:
        """
        Return all nodes of this page tree.
        """
        return self.fixed_nodes.values()

    def get_fixed_tree_of_page(
        self,
        node_id: int | None = None,
    ) -> Iterable[ShadowInstance[Page]]:
        """
        Yield all nodes of the same page tree as the node specified by id in order (fixed).
        If no ``node_id`` is specified, nodes from all trees are considered.
        """
        tree_ids = (
            [self.fixed_nodes[node_id].tree_id]
            if node_id is not None
            else range(1, len(self.trees) + 1)
        )
        for tree_id in tree_ids:
            node = self.trees[tree_id - 1]
            yield from self.yield_subtree(node.pk)

    def yield_subtree(self, node_id: int) -> Iterable[ShadowInstance[Page]]:
        """
        Yield all nodes of the subtree as the node specified by id in order (fixed).
        """
        node = self.fixed_nodes[node_id]
        yield node
        for child_id in node.fixed_children:
            yield from self.yield_subtree(child_id)

    def fix_values(self) -> None:
        """
        Recalculate ``lft``, ``rgt`` and ``depth`` values for the reconstructed hierarchical structure.
        """
        for root_node in self.trees:
            self.fix_values_on_subtree(root_node.pk, 1, 1)

    def fix_values_on_subtree(self, node_id: int, counter: int, depth: int) -> int:
        """
        Recalculate ``lft``, ``rgt`` and ``depth`` values for the subtree of the reconstructed hierarchical structure.
        """
        node = self.fixed_nodes[node_id]
        node.lft = counter
        node.depth = depth
        # Assure that the child nodes are ordered by old lft value
        node.fixed_children.sort(key=lambda node_id: self.fixed_nodes[node_id].lft)
        for child_id in node.fixed_children:
            counter = self.fix_values_on_subtree(child_id, counter + 1, depth + 1)
        node.rgt = counter + 1
        return counter + 1
