from django.db import models
from django.utils import timezone
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from .language import Language


class LanguageTree(MPTTModel):

    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    parent = TreeForeignKey('self',
                            blank=True,
                            null=True,
                            related_name='children')
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
