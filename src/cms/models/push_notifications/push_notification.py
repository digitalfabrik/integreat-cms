from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..regions.region import Region
from .push_notification_channel import PushNotificationChannel
from ...constants.push_notifications import PN_MODES


class PushNotification(models.Model):
    """
    Data model representing a push notification
    """

    region = models.ForeignKey(
        Region,
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
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``PushNotification object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the event
        :rtype: str
        """
        default_translation = self.translations.filter(
            language=self.region.default_language
        ).first()
        if default_translation:
            return default_translation.title
        return repr(self)

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<PushNotification: PushNotification object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the event
        :rtype: str
        """
        return f"<PushNotification (id: {self.id}, channel: {self.channel.name}, region: {self.region.slug})>"

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
