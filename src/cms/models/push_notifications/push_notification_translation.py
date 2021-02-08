from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class PushNotificationTranslation(models.Model):
    """
    Data model representing a push notification translation
    """

    title = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_("title"),
    )
    text = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_("content"),
    )
    language = models.ForeignKey(
        "Language",
        on_delete=models.CASCADE,
        related_name="push_notification_translations",
        verbose_name=_("language"),
    )
    push_notification = models.ForeignKey(
        "PushNotification",
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("push notification"),
    )
    created_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <PushNotificationTranslation object at 0xDEADBEEF>

        :return: The string representation (in this case the title) of the push notification translation
        :rtype: str
        """
        return self.title

    class Meta:
        #: The verbose name of the model
        verbose_name = _("push notification translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("push notification translations")
        #: The default permissions for this model
        default_permissions = ()
        #: Sets of field names that, taken together, must be unique
        unique_together = ["push_notification", "language"]
