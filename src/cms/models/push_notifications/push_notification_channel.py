from django.db import models


class PushNotificationChannel(models.Model):
    """
    Data model representing a push notification channels

    :param channel: The channel of the push notification
    """

    name = models.CharField(max_length=60)

    def __str__(self):
        """
        This overwrites the default Python __str__ method, returns the channel name

        :return: channel name
        :rtype: str
        """
        return self.name

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
            (
                "manage_push_notification_channels",
                "Can manage push notification channels",
            ),
        )
