from django.db import models
from django.conf import settings
from django.utils import timezone

from .accommodation import Accommodation
from ..languages.language import Language
from ...constants import status


class AccommodationTranslation(models.Model):
    """
    Translation of accommodation fields
    """
    rules_of_accommodation = models.TextField()
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=200, blank=True, allow_unicode=True)
    accommodation = models.ForeignKey(
        Accommodation,
        related_name='accommodation_translations',
        null=True,
        on_delete=models.SET_NULL
    )
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
        return self.accommodation

    @property
    def permalink(self):
        return '/'.join([
            self.accommodation.region.slug,
            self.language.code,
            'accommodations',
            self.slug
        ])

    class Meta:
        default_permissions = ()
