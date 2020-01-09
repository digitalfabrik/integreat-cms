"""
Model to define a Language
"""
from django.db import models
from django.utils import timezone

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from .language import Language
from ..regions.region import Region


class LanguageTreeNode(MPTTModel):
    """Class defining a LanguageTree database object.

    Args:
        MPTTModel ([type]): Inheritance of MPTT library to create hierarchically organized data
    """

    language = models.ForeignKey(
        Language,
        related_name='language_tree_nodes',
        on_delete=models.PROTECT
    )
    parent = TreeForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='children',
        on_delete=models.PROTECT
    )
    region = models.ForeignKey(Region, related_name='language_tree_nodes', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def code(self):
        return self.language.code

    @property
    def native_name(self):
        return self.language.native_name

    @property
    def english_name(self):
        return self.language.english_name

    # name of the language in the current backend language
    @property
    def translated_name(self):
        return self.language.translated_name

    @property
    def text_direction(self):
        return self.language.text_direction

    @property
    def depth(self):
        """Provide level of inheritance

        Returns:
            Int : Number of ancestors
        """

        return len(self.get_ancestors())

    class Meta:
        unique_together = (('language', 'region', ), )
        default_permissions = ()
        permissions = (
            ('manage_language_tree', 'Can manage language tree'),
        )

    def __str__(self):
        """Function that provides a string representation of this object

        Returns: String
        """
        return self.language.english_name
