"""Model for Push Notifications
"""
from django.db import models
from django.utils import timezone

from .site import Site
from .language import Language


class PushNotification(models.Model):
    """Class representing the Push Notification base model

    Args:
        models : Databas model inherit from the standard django models
    """
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    channel = models.CharField(max_length=60)
    draft = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)


class PushNotificationTranslation(models.Model):
    """Class representing the Translation of a Push Notification

    Args:
        models : Databas model inherit from the standard django models
    """
    title = models.CharField(max_length=250)
    text = models.CharField(max_length=250)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    push_notification = models.ForeignKey(PushNotification, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
