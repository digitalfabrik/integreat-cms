"""
Model to define a Language
"""
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from .region import Region


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
    native_name = models.CharField(max_length=250, blank=False)
    english_name = models.CharField(max_length=250, blank=False)
    text_direction = models.CharField(default=DIRECTION[0][0], choices=DIRECTION, max_length=3)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    # name of the language in the current backend language
    @property
    def translated_name(self):
        return _(self.english_name)

    def __str__(self):
        """Function that provides a string representation of this object

        Returns: String
        """
        return self.english_name

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
