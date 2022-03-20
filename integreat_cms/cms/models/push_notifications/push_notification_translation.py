from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from ..languages.language import Language
from .push_notification import PushNotification


class PushNotificationTranslation(AbstractBaseModel):
    """
    Data model representing a push notification translation
    """

    title = models.CharField(
        max_length=250,
        verbose_name=_("title"),
    )
    text = models.TextField(
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
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    @classmethod
    def search(cls, region, language_slug, query):
        """
        Searches for all push notifications which match the given `query` in their title.
        :param region: The current region
        :type region: ~integreat_cms.cms.models.regions.region.Region
        :param language_slug: The language slug
        :type language_slug: str
        :param query: The query string used for filtering the push notifications
        :type query: str
        :return: A query for all matching objects
        :rtype: ~django.db.models.QuerySet
        """
        return cls.objects.filter(
            push_notification__region=region,
            language__slug=language_slug,
            title__icontains=query,
        )

    def get_absolute_url(self):
        """
        Generates the absolute url to a news object in the app

        :return: The link to the news
        :rtype: str
        """
        return f"/{self.push_notification.region.slug}/{self.language.slug}/{self.push_notification.channel}/local/{self.id}"

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``PushNotificationTranslation object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the event
        :rtype: str
        """
        return self.title

    def get_repr(self):
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
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["push_notification__pk", "language__pk", "language"]
        #: The default permissions for this model
        default_permissions = ()
        #: Sets of field names that, taken together, must be unique
        unique_together = ["push_notification", "language"]
