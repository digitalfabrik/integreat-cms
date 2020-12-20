from django.db import models
from django.utils.translation import ugettext_lazy as _

from .push_notification_channel import PushNotificationChannel
from ...constants.push_notifications import PN_MODES


class PushNotification(models.Model):
    """
    Data model representing a push notification
    """

    region = models.ForeignKey(
        "Region",
        on_delete=models.CASCADE,
        related_name="push_notifications",
        verbose_name=_("region"),
    )
    channel = models.ForeignKey(
        PushNotificationChannel,
        on_delete=models.CASCADE,
        related_name="push_notifications",
        verbose_name=_("channel"),
    )
    draft = models.BooleanField(
        default=True,
        verbose_name=_("draft"),
        help_text=_(
            "Whether or not the push notification is a draft (drafts cannot be sent)"
        ),
    )
    #: :obj:`None` if the push notification is not yet sent
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("sent date"),
        help_text=_("The date and time when the push notification was sent."),
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )
    #: Manage choices in :mod:`cms.constants.push_notifications`
    mode = models.CharField(
        max_length=128,
        choices=PN_MODES,
        verbose_name=_("mode"),
        help_text=_(
            "Sets behavior for dealing with not existing push notification translations"
        ),
    )

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
        #: The verbose name of the model
        verbose_name = _("push notification")
        #: The plural verbose name of the model
        verbose_name_plural = _("push notifications")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (
            ("view_push_notifications", "Can view push notifications"),
            ("edit_push_notifications", "Can edit push notifications"),
            ("send_push_notifications", "Can send push notifications"),
        )
