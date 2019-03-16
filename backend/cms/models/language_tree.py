"""
Model to define a language tree
"""

from django.db import models
from django.utils import timezone
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from .language import Language


class LanguageTree(MPTTModel):
    """Class defining a LanguageTree database object.

    Args:
        MPTTModel ([type]): Inheritance of MPTT library to create hierachical organized data
    """

    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    parent = TreeForeignKey('self',
                            blank=True,
                            null=True,
                            related_name='children',
                            on_delete=models.PROTECT)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
