from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cacheops import invalidate_model
from db_mutex import DBMutexError, DBMutexTimeoutError
from db_mutex.db_mutex import db_mutex
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from treebeard.exceptions import InvalidPosition
from treebeard.ns_tree import NS_Node, NS_NodeManager

if TYPE_CHECKING:
    from typing import Any

    from treebeard.ns_tree import NS_NodeQuerySet

from ..constants import position
from .abstract_base_model import AbstractBaseModel

logger = logging.getLogger(__name__)


class AbstractTreeNodeManager(NS_NodeManager):
    """
    Custom manager adding a stdout message to ``AbstractTreeNode.objects.create()``
    """

    def create(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """
        Create an object. Direct use is discouraged, use :meth:`treebeard.models.Node.add_root`,
        :meth:`treebeard.models.Node.add_child` or :meth:`treebeard.models.Node.add_sibling` instead.
        """
        obj = super().create(*args, **kwargs)
        mptt_props = ("lft", "rgt", "tree_id", "depth")
        positions = (
            "first-child",
            "last-child",
            "left",
            "right",
            "first-sibling",
            "last-sibling",
        )
        arguments = list(args) + [
            f"{k}={repr(v)}" for k, v in kwargs.items() if k not in mptt_props
        ]

        BOLD = "\033[1m"
        RESET = "\033[0m"

        def b(string):  # type: ignore[no-untyped-def]
            return f"{BOLD}{string}{RESET}"

        print(
            f"""
#### {BOLD}Don't use {obj.__class__.__name__}.objects.create().{RESET} To avoid collisions from manually setting {b('lft')}, {b('rgt')}, {b('tree_id')} and {b('depth')} please use one of the following:
     {obj.__class__.__name__}{b('.add_root(')}{', '.join(arguments)})
     some_parent_node{b('.add_child(')}{', '.join(arguments)})
     some_sibling_node{BOLD}.add_sibling(pos={' | '.join([repr(p) for p in positions])},{RESET}  {', '.join(arguments)})
     More details at https://django-treebeard.readthedocs.io/en/latest/api.html#treebeard.models.Node.add_root
        """
        )
        return obj


# pylint: disable=attribute-defined-outside-init
class AbstractTreeNode(NS_Node, AbstractBaseModel):
    """
    Abstract data model representing a tree node within a region.
    """

    objects = AbstractTreeNodeManager()

    # This field isn't strictly necessary since the hierarchical data is already contained in the lft & rgt fields
    # However, it facilitates some tree operations.
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="children",
        verbose_name=_("parent"),
    )
    region = models.ForeignKey(
        "cms.Region",
        on_delete=models.CASCADE,
        verbose_name=_("region"),
    )

    @classmethod
    def get_region_root_nodes(cls, region_slug: str) -> NS_NodeQuerySet:
        """
        Get all root nodes of a specific region

        :param region_slug: The slug of the requested :class:`~integreat_cms.cms.models.regions.region.Region`
        :return: A queryset containing the root nodes in the tree.
        """
        return super().get_root_nodes().filter(region__slug=region_slug)

    def add_child(self, **kwargs: Any) -> AbstractTreeNode:
        r"""
        Adds a child to the node

        :param \**kwargs: The supplied keyword arguments
        :return: The new child
        """
        # Adding a child can modify all other nodes via raw sql queries (which are not recognized by cachalot),
        # so we have to invalidate the whole model manually.
        invalidate_model(self.__class__)
        child = super().add_child(**kwargs)
        invalidate_model(self.__class__)
        return child

    def add_sibling(self, pos: str | None = None, **kwargs: Any) -> AbstractTreeNode:
        r"""
        Adds a new node as a sibling to the current node object

        :param pos: The position of the new sibling
        :param \**kwargs: The supplied keyword arguments
        :return: The new sibling
        """
        # Adding a sibling can modify all other nodes via raw sql queries (which are not recognized by cachalot),
        # so we have to invalidate the whole model manually.
        invalidate_model(self.__class__)
        sibling = super().add_sibling(pos=pos, **kwargs)
        invalidate_model(self.__class__)
        return sibling

    @classmethod
    def get_tree(cls, parent: AbstractTreeNode | None = None) -> NS_NodeQuerySet:
        """
        Get the tree of a specific parent node

        :param parent: The parent node of which the tree should be returned (optional, if no parent is given, all trees
                       are returned.)
        :return: A :class:`~django.db.models.query.QuerySet` of nodes ordered as DFS, including the parent.
        """
        if not parent:
            logger.debug(
                "Tree of %s requested without parent parameter. "
                "This returns all elements of all regions and is probably not what you want. "
                "Use get_region_tree() instead.",
                cls,
            )
        return super().get_tree(parent=parent)

    @classmethod
    def get_region_tree(cls, region_slug: str) -> NS_NodeQuerySet:
        """
        Get the tree of a specific region

        :param region_slug: The slug of the requested :class:`~integreat_cms.cms.models.regions.region.Region`
        :return: A :class:`~django.db.models.query.QuerySet` of nodes ordered as DFS, including the parent.
        """
        return cls.get_tree().filter(region__slug=region_slug)

    @cached_property
    def region_siblings(self) -> NS_NodeQuerySet:
        """
        Get all siblings of a specific node in its region

        :return: A :class:`~django.db.models.query.QuerySet` of all the node's siblings, including the node itself.
        """
        if self.lft == 1:
            return self.get_region_root_nodes(region_slug=self.region.slug)
        return super().get_siblings()

    @cached_property
    def prev_region_sibling(self) -> AbstractTreeNode | None:
        """
        Get the previous node's sibling, or None if it was the leftmost sibling.

        :return: The previous node's sibling in its region
        """
        siblings = self.region_siblings
        ids = [obj.pk for obj in siblings]
        if self.pk in ids and (idx := ids.index(self.pk)) > 0:
            return siblings[idx - 1]
        return None

    @cached_property
    def next_region_sibling(self) -> AbstractTreeNode | None:
        """
        Get the next node's sibling, or None if it was the rightmost sibling.

        :return: The next node's sibling in its region
        """
        siblings = self.region_siblings
        ids = [obj.pk for obj in siblings]
        if self.pk in ids and (idx := ids.index(self.pk)) < len(siblings) - 1:
            return siblings[idx + 1]
        return None

    def get_cached_ancestors(
        self, include_self: bool = False
    ) -> list[AbstractTreeNode]:
        """
        Get the cached ancestors of a specific node

        :param include_self: Whether the current node should be included in the result (defaults to ``False``)
        :return: A :class:`~django.db.models.query.QuerySet` containing the current node object's ancestors, starting by
                 the root node and descending to the parent.
        """
        if not hasattr(self, "_cached_ancestors"):
            self._cached_ancestors = list(self.get_ancestors())
        if include_self:
            return [*self._cached_ancestors, self]
        return self._cached_ancestors

    @cached_property
    def cached_parent(self) -> AbstractTreeNode | None:
        """
        Get the parent node of the current node object.
        Caches the result in the object itself to help in loops.

        :return: The parent of the node
        """
        if self.is_root():
            return None
        return self.get_cached_ancestors()[-1]

    def get_cached_descendants(
        self, include_self: bool = False
    ) -> list[AbstractTreeNode]:
        """
        Get the cached descendants of a specific node

        :param include_self: Whether the current node should be included in the result (defaults to ``False``)
        :return: A :class:`~django.db.models.query.QuerySet` containing the current node object's ancestors, starting by
                 the root node and descending to the parent.
        """
        if not hasattr(self, "_cached_descendants"):
            self._cached_descendants = list(self.get_descendants())
        if include_self:
            return [self, *self._cached_descendants]
        return self._cached_descendants

    @cached_property
    def cached_children(self) -> list[AbstractTreeNode]:
        """
        Get all cached children

        :returns: A list of all the node's cached children
        """
        if not hasattr(self, "_cached_children"):
            if hasattr(self, "_cached_descendants"):
                self._cached_children = [
                    descendant
                    for descendant in self._cached_descendants
                    if descendant.depth == self.depth + 1
                ]
            else:
                self._cached_children = list(self.get_children())
        return self._cached_children

    def get_tree_max_depth(self, max_depth: int = 1) -> NS_NodeQuerySet:
        """
        Return all descendants with depth less or equal to max depth relative to this nodes depth

        :param max_depth: The nodes maximum depth in the tree
        :return: This node including its descendants with relative max depth
        """
        return self.__class__.get_tree(parent=self).filter(
            depth__lte=self.depth + max_depth
        )

    def move(self, target: AbstractTreeNode, pos: str | None = None) -> None:
        """
        Moves the current node and all it's descendants to a new position
        relative to another node.

        :param target: The target mode which determines the new position
        :param pos: The new position of the page relative to the target
                    (choices: :mod:`~integreat_cms.cms.constants.position`)
        :raises ~treebeard.exceptions.InvalidPosition: If the node is moved to another region
        :raises ~db_mutex.exceptions.DBMutexError: If the DB mutex could not be retrieved
        :raises ~db_mutex.exceptions.DBMutexTimeoutError: If waiting for the DB mutex timed out
        """
        logger.debug("Moving %r to position %r of %r", self, pos, target)
        try:
            with db_mutex(self.__class__.__name__):
                # Do not allow to move a node outside its region, but allow
                # moving as siblings of root nodes (because it's a separate tree)
                if self.region != target.region and not (
                    target.is_root()
                    and pos
                    in [
                        position.LEFT,
                        position.RIGHT,
                        position.FIRST_SIBLING,
                        position.LAST_SIBLING,
                    ]
                ):
                    raise InvalidPosition(
                        _(
                            'The node "{}" in region "{}" cannot be moved to "{}".'
                        ).format(self, self.region, target.region)
                    )
                # Moving a node can modify all other nodes via raw sql queries (which are not recognized by cachalot),
                # so we have to invalidate the whole model manually.
                invalidate_model(self.__class__)
                super().move(target, pos)
        except DBMutexError as e:
            raise DBMutexError(
                _('Could not change position in tree of "{}".').format(self)
            ) from e
        except DBMutexTimeoutError as e:
            raise DBMutexTimeoutError(
                _('Could not change position in tree of "{}".').format(self)
            ) from e
        invalidate_model(self.__class__)

        # Reload 'self' because lft/rgt may have changed
        self.refresh_from_db()
        # Update parent to fix inconsistencies between tree fields
        new_parent = self.get_parent(update=True)
        logger.debug("Updating parent field from %r to %r", self.parent, new_parent)
        self.parent = new_parent
        self.save()

    @classmethod
    def find_problems(cls) -> None:
        """
        Checks for problems in the tree structure.

        This dummy method definition exists to silence pylint's warning:
        Method 'find_problems' is abstract in class 'Node' but is not overridden (abstract-method)
        """

    @classmethod
    def fix_tree(cls) -> None:
        """
        Solves problems that can appear when transactions are not used and
        a piece of code breaks, leaving the tree in an inconsistent state.

        This dummy method definition exists to silence pylint's warning:
        Method 'fix_tree' is abstract in class 'Node' but is not overridden (abstract-method)
        """

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<AbstractTreeNode: AbstractTreeNode object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the tree node
        """
        parent_str = f", parent: {self.parent_id}" if self.parent_id else ""
        region_str = f", region: {self.region.slug}" if self.region else ""
        return f"<{type(self).__name__} (id: {self.id}{parent_str}{region_str})>"

    class Meta:
        #: Abstract model
        abstract = True
