from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ..languages.language import Language
from .push_notification import PushNotification


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
        Language,
        on_delete=models.CASCADE,
        related_name="push_notification_translations",
        verbose_name=_("language"),
    )
    push_notification = models.ForeignKey(
        PushNotification,
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
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``PushNotificationTranslation object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the event
        :rtype: str
        """
        return self.title

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<PushNotificationTranslation: PushNotificationTranslation object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the event
        :rtype: str
        """
        return f"<PushNotificationTranslation (id: {self.id}, push_notification_id: {self.push_notification.id}, title: {self.title})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("push notification translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("push notification translations")
        #: The default permissions for this model
        default_permissions = ()
        #: Sets of field names that, taken together, must be unique
        unique_together = ["push_notification", "language"]
