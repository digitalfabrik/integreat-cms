from django.db import models
from django.utils.translation import ugettext_lazy as _


class PushNotificationChannel(models.Model):
    """
    Data model representing a push notification channels
    """

    name = models.CharField(max_length=60, verbose_name=_("name"))

    def __str__(self):
        """
        This overwrites the default Python __str__ method, returns the channel name

        :return: channel name
        :rtype: str
        """
        return self.name

    class Meta:
        #: The verbose name of the model
        verbose_name = _("push notification channel")
        #: The plural verbose name of the model
        verbose_name_plural = _("push notification channels")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (
            (
                "manage_push_notification_channels",
                "Can manage push notification channels",
            ),
        )
