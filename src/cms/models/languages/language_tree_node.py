from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel, raise_if_unsaved

from django.db import models
from django.utils import timezone

from .language import Language
from ..regions.region import Region


class LanguageTreeNode(MPTTModel):
    """
    Data model representing a region's language tree. Each tree node is a single object instance and the whole tree is
    identified by the root node. The base functionality inherits from the package `django-mptt
    <https://django-mptt.readthedocs.io/en/latest/index.html>`_ (Modified Preorder Tree Traversal).

    :param id: The database id of the language tree node
    :param active: Whether or not it should be possible to create new pages in this language and content of this
                   language should be delivered via the API
    :param created_date: The date and time when the language tree node was created
    :param last_updated: The date and time when the language tree node was last updated

    Fields inherited from the MPTT model (see :doc:`models` for more information):

    :param tree_id: The id of this language tree (all nodes of one language tree share this id)
    :param lft: The left neighbour of this node
    :param rght: The right neighbour of this node
    :param level: The depth of the node. Root nodes are level `0`, their immediate children are level `1`, their
                  immediate children are level `2` and so on...

    Relationship fields:

    :param parent: The parent node of this node (related name: ``children``)
    :param language: Language this tree node refers to (related name: ``language_tree_nodes``)
    :param region: The region this node belongs to (related name: ``language_tree_nodes``)

    Reverse relationships:

    :param children: The children of this language tree node
    """

    language = models.ForeignKey(
        Language, related_name="language_tree_nodes", on_delete=models.PROTECT
    )
    parent = TreeForeignKey(
        "self", blank=True, null=True, related_name="children", on_delete=models.PROTECT
    )
    region = models.ForeignKey(
        Region, related_name="language_tree_nodes", on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def code(self):
        """
        Returns the code of this node's language

        :return: The language code of this language node
        :rtype: str
        """
        return self.language.code

    @property
    def native_name(self):
        """
        Returns the native name of this node's language

        :return: The native name of this language node
        :rtype: str
        """
        return self.language.native_name

    @property
    def english_name(self):
        """
        Returns the name of this node's language in English

        :return: The English name of this language node
        :rtype: str
        """
        return self.language.english_name

    @property
    def translated_name(self):
        """
        Returns the name of this node's language in the current backend language

        :return: The translated name of this language node
        :rtype: str
        """
        return self.language.translated_name

    @property
    def text_direction(self):
        """
        Returns the text direction (e.g. left-to-right) of this node's language

        :return: The text direction name of this language node
        :rtype: str
        """
        return self.language.text_direction

    @property
    def depth(self):
        """
        Counts how many ancestors the node has. If the node is the root node, its depth is `0`.

        :return: The depth of this language node
        :rtype: str
        """
        return len(self.get_ancestors())

    # Explicitly define functions to show documentation of base model
    @raise_if_unsaved
    def get_ancestors(self, ascending=False, include_self=False):
        return super().get_ancestors(ascending, include_self)

    # pylint: disable=useless-super-delegation
    @raise_if_unsaved
    def get_family(self):
        return super().get_family()

    @raise_if_unsaved
    def get_children(self):
        return super().get_children()

    @raise_if_unsaved
    def get_descendants(self, include_self=False):
        return super().get_descendants(include_self)

    def get_descendant_count(self):
        return super().get_descendant_count()

    @raise_if_unsaved
    def get_root(self):
        return super().get_root()

    # pylint: disable=useless-super-delegation
    def insert_at(
        self,
        target,
        position="first-child",
        save=False,
        allow_existing_pk=False,
        refresh_target=True,
    ):
        return super().insert_at(
            target, position, save, allow_existing_pk, refresh_target
        )

    # pylint: disable=useless-super-delegation
    def move_to(self, target, position="first-child"):
        return super().move_to(target, position)

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <LanguageTreeNode object at 0xDEADBEEF>

        :return: The string representation (in this case the English name) of the node's language
        :rtype: str
        """
        return self.language.english_name

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param unique_together: There cannot be two language tree nodes with the same region and language
        :type default_permissions: tuple

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple

        :param permissions: The custom permissions for this model
        :type permissions: tuple
        """

        unique_together = (
            (
                "language",
                "region",
            ),
        )
        default_permissions = ()
        permissions = (("manage_language_tree", "Can manage language tree"),)
