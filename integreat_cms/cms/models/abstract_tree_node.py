import logging
from django.db import models
from django.utils.translation import ugettext_lazy as _

from cacheops import invalidate_model

from treebeard.exceptions import InvalidPosition
from treebeard.ns_tree import NS_Node, get_result_class

from ..constants import position

logger = logging.getLogger(__name__)


class AbstractTreeNode(NS_Node):
    """
    Abstract data model representing a tree node within a region.
    """

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

    def save(self, *args, **kwargs):
        # Update parent to fix inconsistencies between tree fields
        if self.id:
            self.parent = self.get_parent()
        super().save(*args, **kwargs)

    @classmethod
    def get_region_root_nodes(cls, region_slug):
        """
        Get all root nodes of a specific region

        :param region_slug: The slug of the requested :class:`~integreat_cms.cms.models.regions.region.Region`
        :type region_slug: str

        :return: A queryset containing the root nodes in the tree.
        :rtype: ~treebeard.ns_tree.NS_NodeQuerySet
        """
        return super().get_root_nodes().filter(region__slug=region_slug)

    def add_child(self, **kwargs):
        r"""
        Adds a child to the node

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The new child
        :rtype: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode
        """
        # Adding a child can modify all other nodes via raw sql queries (which are not recognized by cachalot),
        # so we have to invalidate the whole model manually.
        invalidate_model(self.__class__)
        child = super().add_child(**kwargs)
        invalidate_model(self.__class__)
        return child

    def add_sibling(self, pos=None, **kwargs):
        r"""
        Adds a new node as a sibling to the current node object

        :param pos: The position of the new sibling
        :type pos: str

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The new sibling
        :rtype: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode
        """
        # Adding a sibling can modify all other nodes via raw sql queries (which are not recognized by cachalot),
        # so we have to invalidate the whole model manually.
        invalidate_model(self.__class__)
        sibling = super().add_sibling(pos=pos, **kwargs)
        invalidate_model(self.__class__)
        return sibling

    @classmethod
    def get_tree(cls, parent=None):
        """
        Get the tree of a specific parent node

        :param parent: The parent node of which the tree should be returned (optional, if no parent is given, all trees
                       are returned.)
        :type parent: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode

        :return: A :class:`~django.db.models.query.QuerySet` of nodes ordered as DFS, including the parent.
        :rtype: ~treebeard.ns_tree.NS_NodeQuerySet
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
    def get_region_tree(cls, region_slug):
        """
        Get the tree of a specific region

        :param region_slug: The slug of the requested :class:`~integreat_cms.cms.models.regions.region.Region`
        :type region_slug: str

        :return: A :class:`~django.db.models.query.QuerySet` of nodes ordered as DFS, including the parent.
        :rtype: ~treebeard.ns_tree.NS_NodeQuerySet
        """
        return cls.get_tree().filter(region__slug=region_slug)

    def get_region_siblings(self):
        """
        Get all siblings of a specific node in its region

        :return: A :class:`~django.db.models.query.QuerySet` of all the node's siblings, including the node itself.
        :rtype: ~treebeard.ns_tree.NS_NodeQuerySet
        """
        if self.lft == 1:
            return self.get_region_root_nodes(region_slug=self.region.slug)
        return super().get_siblings()

    def get_prev_region_sibling(self):
        """
        Get the previous node's sibling, or None if it was the leftmost sibling.

        :return: The previous node's sibling in its region
        :rtype: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode
        """
        siblings = self.get_region_siblings()
        ids = [obj.pk for obj in siblings]
        if self.pk in ids:
            idx = ids.index(self.pk)
            if idx > 0:
                return siblings[idx - 1]
        return None

    def get_next_region_sibling(self):
        """
        Get the next node's sibling, or None if it was the rightmost sibling.

        :return: The next node's sibling in its region
        :rtype: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode
        """
        siblings = self.get_region_siblings()
        ids = [obj.pk for obj in siblings]
        if self.pk in ids:
            idx = ids.index(self.pk)
            if idx < len(siblings) - 1:
                return siblings[idx + 1]
        return None

    # pylint: disable=arguments-differ
    def get_ancestors(self, include_self=False):
        """
        Get all ancestors of a specific node

        :param include_self: Whether the current node should be included in the result (defaults to ``False``)
        :type include_self: bool

        :return: A :class:`~django.db.models.query.QuerySet` containing the current node object's ancestors, starting by
                 the root node and descending to the parent.
        :rtype: ~treebeard.ns_tree.NS_NodeQuerySet
        """
        if include_self:
            return get_result_class(self.__class__).objects.filter(
                tree_id=self.tree_id, lft__lte=self.lft, rgt__gte=self.rgt
            )
        return super().get_ancestors()

    def get_parent(self, update=False):
        """
        Get the parent node of the current node object.
        Caches the result in the object itself to help in loops.

        :param update: Whether the cache should be invalidated (defaults to ``False``)
        :type update: bool

        :return: The parent of the node
        :rtype: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode
        """
        if self.is_root():
            return None
        try:
            if update:
                del self._cached_parent_obj
            else:
                return self._cached_parent_obj
        except AttributeError:
            pass
        # parent = our most direct ancestor
        # pylint: disable=attribute-defined-outside-init
        self._cached_parent_obj = self.get_ancestors()[-1]
        return self._cached_parent_obj

    # pylint: disable=arguments-differ
    def get_descendants(self, include_self=False):
        """
        Get all descendants of a specific node

        :param include_self: Whether the current node should be included in the result (defaults to ``False``)
        :type include_self: bool

        :return: A :class:`~django.db.models.query.QuerySet` of all the node's descendants as DFS
        :rtype: ~treebeard.ns_tree.NS_NodeQuerySet
        """
        if self.is_leaf():
            return get_result_class(self.__class__).objects.none()
        tree = self.__class__.get_tree(parent=self)
        if include_self:
            return tree
        return tree.exclude(pk=self.pk)

    def get_descendants_max_depth(self, include_self=False, max_depth=1):
        """
        Return all descendants with depth less or equal to max depth relative to this nodes depth

        :param include_self: Whether the current node should be included in the result (defaults to ``False``)
        :type include_self: bool

        :param max_depth: The nodes maximum depth in the tree
        :type max_depth: int

        :return: All descendants of this node with relative max depth
        :rtype: ~treebeard.ns_tree.NS_NodeQuerySet [ ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode ]
        """
        return self.get_descendants(include_self=include_self).filter(
            depth__lte=self.depth + max_depth
        )

    def move(self, target, pos=None):
        """
        Moves the current node and all it's descendants to a new position
        relative to another node.

        :param target: The target mode which determines the new position
        :type target: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode

        :param pos: The new position of the page relative to the target
                    (choices: :mod:`~integreat_cms.cms.constants.position`)
        :type pos: str

        :raises ~treebeard.exceptions.InvalidPosition: If the node is moved to another region
        """
        # Do not allow to move a node outside its region
        if self.region != target.region:
            # Allow moving as siblings of root nodes (because it's a separate tree)
            if not (target.is_root() and pos in [position.LEFT, position.RIGHT]):
                raise InvalidPosition(
                    _('The node "{}" in region "{}" cannot be moved to "{}".').format(
                        self, self.region, target.region
                    )
                )
        # Moving a node can modify all other nodes via raw sql queries (which are not recognized by cachalot),
        # so we have to invalidate the whole model manually.
        invalidate_model(self.__class__)
        super().move(target=target, pos=pos)
        invalidate_model(self.__class__)

    @classmethod
    def find_problems(cls):
        """
        Checks for problems in the tree structure.

        This dummy method definition exists to silence pylint's warning:
        Method 'find_problems' is abstract in class 'Node' but is not overridden (abstract-method)
        """

    @classmethod
    def fix_tree(cls):
        """
        Solves problems that can appear when transactions are not used and
        a piece of code breaks, leaving the tree in an inconsistent state.

        This dummy method definition exists to silence pylint's warning:
        Method 'fix_tree' is abstract in class 'Node' but is not overridden (abstract-method)
        """

    class Meta:
        #: Abstract model
        abstract = True
