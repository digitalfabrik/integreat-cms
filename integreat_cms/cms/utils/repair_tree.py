"""
This module contains utilities to repair or detect inconsistencies in a tree
"""
from __future__ import annotations
from collections.abc import Callable

import logging

from django.db import transaction

from ..models import Page
from ..utils.tree_mutex import tree_mutex

logger = logging.getLogger(__name__)


class Printer:
    """
    Select printer for stdout or log file
    """

    def __init__(self, print_func=None, error=None, success=None) -> None:
        """
        Map passed print functions to internal attributes
        """
        self._print = print_func
        self._error = error
        self._success = success
        self._write = None
        self._bold = None

    @property
    def print(self) -> Callable[str]:
        """
        Return regular print w/o coloring
        """
        if not self._print:
            return logger.debug
        return self._print

    @print.setter
    def print(self, new: Callable[str]) -> None:
        """
        Print w/o styling
        """
        self._print = new

    @property
    def error(self) -> print:
        """
        Return error print function
        """
        if not self._error:
            return self.print
        return self._error

    @error.setter
    def error(self, new: Callable[str]) -> None:
        """
        Set print function with error styling
        """
        self._error = new

    @property
    def success(self) -> Callable[str]:
        """
        Return success print function
        """
        if not self._success:
            return self.print
        return self._success

    @success.setter
    def success(self, new: Callable[str]) -> None:
        """
        Set print function with success styling
        """
        self._success = new

    @property
    def bold(self) -> Callable[str]:
        """
        Return bold print function
        """
        if not self._bold:
            return lambda x: x
        return self._bold

    @bold.setter
    def bold(self, new: Callable[str]) -> None:
        """
        Set print function for bold font
        """
        self._bold = new

    @property
    def write(self) -> Callable[str]:
        """
        Return write function w/o new line
        """
        if not self._write:
            return self.print
        return self._write

    @write.setter
    def write(self, new: Callable[str]) -> None:
        """
        Set write function w/o new line
        """
        self._write = new


@transaction.atomic
@tree_mutex
def repair_tree(
    page_id: int = 0, commit: bool = False, printer: Printer = Printer()
) -> None:
    mptt_fixer = MPTTFixer()

    if page_id:
        # show tree of selected page
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist as e:
            raise ValueError(f'The page with id "{page_id}" does not exist.') from e
        root_nodes = [mptt_fixer.get_fixed_root_node(page_id)]
    else:
        root_nodes = mptt_fixer.get_fixed_root_nodes()

    for root_node in root_nodes:
        action = "Fixing" if commit else "Detecting problems in"
        printer.print(f"{action} tree with id {root_node.tree_id}...")
        for tree_node in mptt_fixer.get_fixed_tree_of_page(root_node.pk):
            # the first node is always the root node
            print_changed_fields(
                Page.objects.get(id=tree_node.pk), tree_node.lft, tree_node.rgt, printer
            )

    if commit:
        for page in mptt_fixer.get_fixed_tree_nodes():
            page.save()


def print_changed_fields(
    tree_node: Page, left: int, right: int, printer: Printer = Printer()
) -> None:
    """
    Check whether the tree fields are correct

    :param tree_node: The current node
    :param left: The new left value of the node
    :param right: The new right value of the node
    :return: Whether the tree fields of the node are valid
    """
    printer.write(printer.bold(f"Page {tree_node.id}:"))
    printer.success(f"\tparent_id: {tree_node.parent_id}")
    if not tree_node.parent or tree_node.tree_id == tree_node.parent.tree_id:
        printer.success(f"\ttree_id: {tree_node.tree_id}")
    else:
        printer.error(f"\ttree_id: {tree_node.tree_id} → {tree_node.parent.tree_id}")
    if tree_node.parent_id:
        if tree_node.depth == tree_node.parent.depth + 1:
            printer.success(f"\tdepth: {tree_node.depth}")
        else:
            printer.error(f"\tdepth: {tree_node.depth} → {tree_node.parent.depth + 1}")
    elif tree_node.depth == 1:
        printer.success(f"\tdepth: {tree_node.depth}")
    else:
        printer.error(f"\tdepth: {tree_node.depth} → 1")
    if tree_node.lft == left:
        printer.success(f"\tlft: {tree_node.lft}")
    else:
        printer.error(f"\tlft: {tree_node.lft} → {left}")
    if tree_node.rgt == right:
        printer.success(f"\trgt: {tree_node.rgt}")
    else:
        printer.error(f"\trgt: {tree_node.rgt} → {right}")


class MPTTFixer:
    """
    eats all nodes and coughs out fixed LFT, RGT and depth values. Uses the parent field
    to fix hierarchy and sorts siblings by (potentially inconsistent) lft.
    """
    def __init__(self) -> None:
        """
        Creates a fixed tree when initializing class but does not save results
        """
        self.broken_nodes: list[Page] = list(Page.objects.all().order_by("tree_id", "lft"))
        # Dictionaries keep the insert order as of Python 3.7
        self.fixed_nodes: dict[int, Page] = {}
        self.fix_root_nodes()
        self.fix_child_nodes()

    def fix_root_nodes(self) -> None:
        """
        extract root nodes and reset lft + rgt values
        """
        tree_counter = 1
        for node in self.broken_nodes:
            if not node.parent_id:
                node.lft = 1
                node.rgt = 2
                node.depth = 1
                node.fixed_children = []
                node.tree_id = tree_counter
                tree_counter = tree_counter + 1
                self.fixed_nodes[node.pk] = node

    def fix_child_nodes(self) -> None:
        """
        Get all remaining (child) nodes, add add them to the new/fixed tree
        """
        for node in self.broken_nodes:
            if node.parent_id:
                parent = self.fixed_nodes[node.parent_id]
                node.fixed_children = []
                node = self.calculate_lft_rgt(node, parent)
                # append fixed node to tree and update ancestors lft/rgt
                self.fixed_nodes[node.pk] = node
                self.fixed_nodes[parent.pk].fixed_children.append(node.pk)
                self.update_ancestors_rgt(node.pk)

    def calculate_lft_rgt(self, node: Page, parent: Page) -> Page:
        """
        add a new node to the existing MPTT structure. As we sorted by lft, we always add
        to the right of existing nodes.
        """
        if not parent.fixed_children:
            # first child node, use lft of parent to calculate node lft/rgt
            node.lft = parent.lft + 1
            node.rgt = node.lft + 1
            node.depth = parent.depth + 1
        else:
            # parent has fixed_children. Get right-most sibling and continue lft from there.
            left_sibling = self.fixed_nodes[parent.fixed_children[-1]]
            node.lft = left_sibling.rgt + 1
            node.rgt = node.lft + 1
            node.depth = left_sibling.depth
        return node

    def update_ancestors_rgt(self, node_id: int) -> None:
        """
        As we only append siblings to the right, we only need to modify the rgt values
        of all ancestors to adopt the new node into the tree.
        """
        node = self.fixed_nodes[node_id]
        while node.parent_id is not None:
            self.fixed_nodes[node.parent_id].rgt = node.rgt + 1
            node = self.fixed_nodes[node.parent_id]

    def get_fixed_root_nodes(self) -> list[Page]:
        """
        Return a list of all fixed root nodes
        """
        for node in self.fixed_nodes.values():
            if node.parent is None:
                yield node

    def get_fixed_root_node(self, page_id: int) -> Page:
        """
        Travel up ancestors of a page until we get the root node
        """
        page = self.fixed_nodes[page_id]
        while page.parent_id is not None:
            page = self.fixed_nodes[page.parent_id]
        return page

    def get_fixed_tree_nodes(self) -> [Page]:
        """
        Yield all page tree nodes
        """
        return self.fixed_nodes.values()

    def get_fixed_tree_of_page(self, node_id: int = None) -> list[Page]:
        """
        get all nodes of page tree, either identfied by one page or the (new) tree ID.
        get all trees if no key is provided.
        """
        if node_id is not None:
            tree_id = self.fixed_nodes[node_id].tree_id
        else:
            tree_id = None
        for node in self.fixed_nodes.values():
            if tree_id is None or node.tree_id == tree_id:
                yield node
