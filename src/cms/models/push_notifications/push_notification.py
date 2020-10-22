from django.db import models
from .push_notification_channel import PushNotificationChannel
from ...constants.push_notifications import PN_MODES


class PushNotification(models.Model):
    """
    Data model representing a push notification

    :param id: The database id of the push notification
    :param channel: The channel of the push notification
    :param draft: Whether or not the push notification is a draft (drafts cannot be sent)
    :param sent_date: The date and time when the push notification was sent (:obj:`None` if the push notification is
                      not yet sent)
    :param created_date: The date and time when the push notification was created
    :param last_updated: The date and time when the push notification was last updated
    :param mode: Sets behavior for dealing with not existing push notification translations

    Relationship fields:

    :param region: The region of the push notification (related name: ``push_notifications``)

    Reverse relationships:

    :param translations: All translations of this push notification
    """

    region = models.ForeignKey(
        "Region", related_name="push_notifications", on_delete=models.CASCADE
    )
    channel = models.ForeignKey(
        PushNotificationChannel,
        related_name="push_notifications",
        on_delete=models.CASCADE,
    )
    draft = models.BooleanField(default=True)
    sent_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    mode = models.CharField(max_length=128, choices=PN_MODES)

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <PushNotification object at 0xDEADBEEF>

        :return: The string representation of the push notification (in this case the title of the first existing
                 push notification translation)
        :rtype: str
        """
        if self.translations.exists():
            return self.translations.first().title
        return ""

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple

        :param permissions: The custom permissions for this model
        :type permissions: tuple
        """

        default_permissions = ()
        permissions = (
            ("view_push_notifications", "Can view push notifications"),
            ("edit_push_notifications", "Can edit push notifications"),
            ("send_push_notifications", "Can send push notifications"),
        )
