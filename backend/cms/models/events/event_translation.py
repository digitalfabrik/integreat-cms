"""Class defining event-related database models

Raises:
    ValidationError: Raised when an value does not match the requirements
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from .event import Event
from ..languages.language import Language
from ...constants import status


class EventTranslation(models.Model):
    """
    Database object representing an event translation
    """

    event = models.ForeignKey(Event, related_name='translations', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200, blank=True, allow_unicode=True)
    status = models.CharField(max_length=6, choices=status.CHOICES, default=status.DRAFT)
    title = models.CharField(max_length=250)
    description = models.TextField()
    language = models.ForeignKey(
        Language,
        related_name='event_translations',
        on_delete=models.CASCADE
    )
    currently_in_translation = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def foreign_object(self):
        return self.event

    @property
    def permalink(self):
        return '/'.join([
            self.event.region.slug,
            self.language.code,
            'events',
            self.slug
        ])

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['event', '-version']
        default_permissions = ()
