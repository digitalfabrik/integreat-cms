"""Model for Point of Interests

"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from .poi import POI
from ..languages.language import Language
from ...constants import status


class POITranslation(models.Model):
    """Translation of an Point of Interest

    Args:
        models : Databas model inherit from the standard django models
    """

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=200, blank=True, allow_unicode=True)
    poi = models.ForeignKey(POI, related_name='translations', null=True,
                            on_delete=models.SET_NULL)
    status = models.CharField(max_length=6, choices=status.CHOICES, default=status.DRAFT)
    short_description = models.CharField(max_length=250)
    description = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    @property
    def foreign_object(self):
        return self.poi

    @property
    def permalink(self):
        return '/'.join([
            self.poi.region.slug,
            self.language.code,
            'pois',
            self.slug
        ])

    class Meta:
        default_permissions = ()
