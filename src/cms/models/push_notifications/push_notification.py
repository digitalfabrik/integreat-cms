"""Model for Push Notifications
"""
from django.db import models


class PushNotification(models.Model):
    """Class representing the Push Notification base model

    Args:
        models : Databas model inherit from the standard django models
    """
    region = models.ForeignKey('Region', related_name='push_notifications', on_delete=models.CASCADE)
    channel = models.CharField(max_length=60)
    draft = models.BooleanField(default=True)
    sent_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.translations.exists():
            return self.translations.first().title
        return ""

    class Meta:
        default_permissions = ()
        permissions = (
            ('view_push_notifications', 'Can view push notification'),
            ('edit_push_notifications', 'Can edit push notification'),
            ('send_push_notifications', 'Can send push notification'),
        )
