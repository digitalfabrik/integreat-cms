from django.contrib.postgres.fields import ArrayField
from django.db import models

from cms.models.language import Language


class Site(models.Model):
    ACTIVE = 'acti'
    HIDDEN = 'hidd'
    ARCHIVED = 'arch'

    STATUS = (
        (ACTIVE, 'Active'),
        (HIDDEN, 'Hidden'),
        (ARCHIVED, 'Archived'),
    )

    title = models.CharField(max_length=200)
    name = models.URLField(max_length=60, unique=True)
    status = models.CharField(max_length=4, choices=STATUS)
    supported_languages = models.ManyToManyField(Language)

    events_enabled = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)
    push_notification_channels = ArrayField(models.CharField(max_length=60))

    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    postal_code = models.CharField(max_length=10)

    admin_mail = models.EmailField()

    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
