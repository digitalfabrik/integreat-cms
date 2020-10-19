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
