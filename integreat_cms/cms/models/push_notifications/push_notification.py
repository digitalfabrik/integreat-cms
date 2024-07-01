"""
The model for the push notification
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models.query import QuerySet

    from .push_notification_translation import PushNotificationTranslation

from ...constants.push_notifications import PN_MODES
from ..abstract_base_model import AbstractBaseModel
from ..languages.language import Language
from ..regions.region import Region


class PushNotification(AbstractBaseModel):
    """
    Data model representing a push notification
    """

    regions = models.ManyToManyField(
        Region,
        related_name="push_notifications",
        verbose_name=_("regions"),
    )
    channel = models.CharField(
        max_length=60,
        choices=settings.FCM_CHANNELS,
        default=settings.FCM_CHANNELS[0][0],
        verbose_name=_("channel"),
    )
    draft = models.BooleanField(
        default=True,
        verbose_name=_("draft"),
        help_text=_("Whether or not the News is a draft (drafts cannot be sent)"),
    )
    #: :obj:`None` if the push notification is not yet sent
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("sent date"),
        help_text=_("The date and time when the News was sent."),
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )
    scheduled_send_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("scheduled send date"),
        help_text=_("The scheduled date for this News to be sent"),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.push_notifications`
    mode = models.CharField(
        max_length=128,
        choices=PN_MODES,
        verbose_name=_("mode"),
        help_text=_("Sets behavior for dealing with not existing News translations"),
    )
    #: Distinct functionalities for templates
    is_template = models.BooleanField(
        default=False,
        verbose_name=_("News template"),
    )
    template_name = models.CharField(
        null=True,
        blank=True,
        max_length=128,
        verbose_name=_("News template name"),
        help_text=_("Provide a distinct name for the template"),
    )

    @cached_property
    def languages(self) -> QuerySet[Language]:
        """
        This property returns a QuerySet of all :class:`~integreat_cms.cms.models.languages.language.Language` objects,
        to which a push notification translation exists.

        :return: QuerySet of all :class:`~integreat_cms.cms.models.languages.language.Language` a push notification is
                 translated into
        """
        return Language.objects.filter(
            push_notification_translations__push_notification=self
        )

    @property
    def backend_translation(self) -> PushNotificationTranslation | None:
        """
        This function returns the translation of this push notification in the current backend language.

        :return: The backend translation of a push notification
        """
        return self.translations.filter(language__slug=get_language()).first()

    @property
    def default_language(self) -> Language:
        """
        This property returns the default language of this push notification
        :return: The default language of the first region
        """
        return self.regions.first().default_language

    @property
    def default_translation(self) -> PushNotificationTranslation:
        """
        This function returns the translation of this push notification in the region's default language.
        Since a push notification can only be created by creating a translation in the default language, this is
        guaranteed to return a push notification translation.

        :return: The default translation of a push notification
        """
        return self.translations.filter(language=self.default_language).first()

    @property
    def best_translation(self) -> PushNotificationTranslation:
        """
        This function returns the translation of this push notification in the current backend language and if it
        doesn't exist, it provides a fallback to the translation in the region's default language.

        :return: The "best" translation of a push notification for displaying in the backend
        """
        backend_translation = self.backend_translation
        return (
            backend_translation
            if backend_translation and backend_translation.title
            else (self.default_translation or self.translations.first())
        )

    @cached_property
    def scheduled_send_date_local(self) -> datetime | None:
        """
        Convert the scheduled send date to local time

        :return: The scheduled send date in local time
        """
        if not self.scheduled_send_date:
            return None
        return timezone.localtime(self.scheduled_send_date)

    @cached_property
    def is_overdue(self) -> bool:
        """
        This property returns whether the notification is overdue based on the retain time setting and
        scheduled_send_date. This method only works for scheduled notifications.

        :return: True if the message is overdue, False otherwise
        """
        if not self.scheduled_send_date:
            return False

        retention_time = timezone.now() - timedelta(
            hours=settings.FCM_NOTIFICATION_RETAIN_TIME_IN_HOURS
        )
        return timezone.localtime(self.scheduled_send_date) <= retention_time

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``PushNotification object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the push notification
        """
        return self.best_translation.title

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<PushNotification: PushNotification object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the push notification
        """
        return f"<PushNotification (id: {self.id}, channel: {self.channel}, regions: {self.regions.values_list('slug', flat=True)})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("push notification")
        #: The plural verbose name of the model
        verbose_name_plural = _("push notifications")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The custom permissions for this model
        permissions = (("send_push_notification", "Can send push notification"),)
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["-created_date"]
