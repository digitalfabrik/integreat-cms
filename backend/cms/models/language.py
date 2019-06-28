"""
Model to define a Language
"""

from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from .site import Site

class Language(models.Model):
    """
    Class to define language database objects

    Args:
        models : Database model inherit from the standard django models
    """

    DIRECTION = (
        ('ltr', _('Left to right')),
        ('rtl', _('Right to left'))
    )

    # We use bcp47 language codes (see https://tools.ietf.org/html/bcp47).
    # The recommended minimum buffer is 35 (see https://tools.ietf.org/html/bcp47#section-4.4.1).
    # It's unlikely that we have language codes longer than 8 characters though.
    code = models.CharField(max_length=8, unique=True, validators=[MinLengthValidator(2)])
    name = models.CharField(max_length=250, blank=False)
    text_direction = models.CharField(default=DIRECTION[0][0], choices=DIRECTION, max_length=3)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Function that provides a string representation of this object

        Returns: String
        """
        return self.name

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_languages', 'Can manage languages'),
        )

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
    site = models.ForeignKey(Site, related_name='language_tree_nodes', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def depth(self):
        """Provide level of inheritance

        Returns:
            Int : Number of ancestors
        """

        return len(self.get_ancestors())

    class Meta:
        unique_together = (('language', 'site', ), )
        default_permissions = ()
        permissions = (
            ('manage_language_tree', 'Can manage language tree'),
        )

    def __str__(self):
        """Function that provides a string representation of this object

        Returns: String
        """
        return self.language.name
