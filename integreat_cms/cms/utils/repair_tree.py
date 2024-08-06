"""
This module contains utilities to repair or detect inconsistencies in a tree
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Iterable

from ..models import Page
from .shadow_instance import ShadowInstance
from .tree_mutex import tree_mutex


@tree_mutex("page")
def repair_tree(
    page_id: int | None = None, commit: bool = False, logging_name: str = __name__
) -> None:
    """
    Fix the tree for a given page, or all trees if no id is given.
    Changes are only written to the database if ``commit`` is set to ``True``.
    For details see :class:`MPTTFixer`.
    """
    logger = logging.getLogger(logging_name)

    mptt_fixer = MPTTFixer()
    root_nodes: Iterable[ShadowInstance[Page]]

    if page_id:
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist as e:
            raise ValueError(f'The page with id "{page_id}" does not exist.') from e
        root_nodes = [mptt_fixer.get_fixed_root_node(page_id)]
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
    tree_node: ShadowInstance[Page], logging_name: str = __name__
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

    def __init__(self) -> None:
        """
        Create a fixed tree, using a :class:`~integreat_cms.cms.utils.shadow_instance.ShadowInstance` of each page.
        """
        self.broken_root_nodes: Iterable[ShadowInstance[Page]] = list(
            map(ShadowInstance, Page.objects.filter(parent=None))
        )
        self.broken_child_nodes: deque[ShadowInstance[Page]] = deque(
            map(ShadowInstance, Page.objects.exclude(parent=None))
        )
        self.fixed_nodes: dict[int, ShadowInstance[Page]] = {}
        self.fix_root_nodes()
        self.fix_child_nodes()

    def fix_root_nodes(self) -> None:
        """
        Extract root nodes and reset ``lft`` and ``rgt`` values.
        """
        for tree_counter, node in enumerate(self.broken_root_nodes, 1):
            node.lft = 1
            node.rgt = 2
            node.depth = 1
            node.fixed_children = []
            node.tree_id = tree_counter
            self.fixed_nodes[node.pk] = node

    def fix_child_nodes(self) -> None:
        """
        Get all remaining (child) nodes and add them to the new/fixed tree.
        """
        while self.broken_child_nodes:
            node = self.broken_child_nodes.popleft()
            if node.parent_id not in self.fixed_nodes:
                self.broken_child_nodes.append(node)
                continue
            parent = self.fixed_nodes[node.parent_id]
            node.fixed_children = []
            node = self.calculate_lft_rgt(node, parent)
            self.fixed_nodes[node.pk] = node
            self.fixed_nodes[parent.pk].fixed_children.append(node.pk)
            self.update_ancestors_rgt(node.pk)

    def calculate_lft_rgt(
        self, node: ShadowInstance[Page], parent: ShadowInstance[Page]
    ) -> ShadowInstance[Page]:
        """
        Add a new node to the existing MPTT structure.
        As we sorted by ``lft``, we always add to the right of existing nodes.
        """
        if not parent.fixed_children:
            node.lft = parent.lft + 1
            node.rgt = node.lft + 1
            node.depth = parent.depth + 1
        else:
            left_sibling = self.fixed_nodes[parent.fixed_children[-1]]
            node.lft = left_sibling.rgt + 1
            node.rgt = node.lft + 1
            node.depth = left_sibling.depth
        return node

    def update_ancestors_rgt(self, node_id: int) -> None:
        """
        Modify the ``rgt`` values of all ancestors of a node.
        As we only append siblings to the right, this is sufficient to adopt the new node into the tree.
        """
        node = self.fixed_nodes[node_id]
        while node.parent_id is not None:
            self.fixed_nodes[node.parent_id].rgt = node.rgt + 1
            node = self.fixed_nodes[node.parent_id]

    def get_fixed_root_nodes(self) -> Iterable[ShadowInstance[Page]]:
        """
        Yield all fixed root nodes.
        """
        for node in self.fixed_nodes.values():
            if node.parent is None:
                yield node

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
        self, node_id: int | None = None
    ) -> Iterable[ShadowInstance[Page]]:
        """
        Yield all nodes of the same page tree as the node specified by id.
        If no ``node_id`` is specified, nodes from all trees are considered.
        """
        tree_id = self.fixed_nodes[node_id].tree_id if node_id is not None else None
        for node in self.fixed_nodes.values():
            if tree_id is None or node.tree_id == tree_id:
                yield node
