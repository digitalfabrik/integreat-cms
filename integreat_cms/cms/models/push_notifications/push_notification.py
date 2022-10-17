"""
The model for the push notificatiion
"""
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import get_language, ugettext_lazy as _

from ...constants.push_notifications import PN_MODES
from ..abstract_base_model import AbstractBaseModel
from ..languages.language import Language
from ..regions.region import Region


class PushNotification(AbstractBaseModel):
    """
    Data model representing a push notification
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="push_notifications",
        verbose_name=_("region"),
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
    #: Manage choices in :mod:`~integreat_cms.cms.constants.push_notifications`
    mode = models.CharField(
        max_length=128,
        choices=PN_MODES,
        verbose_name=_("mode"),
        help_text=_(
            "Sets behavior for dealing with not existing push notification translations"
        ),
    )

    @cached_property
    def languages(self):
        """
        This property returns a QuerySet of all :class:`~integreat_cms.cms.models.languages.language.Language` objects,
        to which a push notification translation exists.

        :return: QuerySet of all :class:`~integreat_cms.cms.models.languages.language.Language` a push notification is
                 translated into
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.languages.language.Language ]
        """
        return Language.objects.filter(
            push_notification_translations__push_notification=self
        )

    @property
    def backend_translation(self):
        """
        This function returns the translation of this push notification in the current backend language.

        :return: The backend translation of a push notification
        :rtype: ~integreat_cms.cms.models.push_notifications.push_notification_translation.PushNotificationTranslation
        """
        return self.translations.filter(language__slug=get_language()).first()

    @property
    def default_translation(self):
        """
        This function returns the translation of this push notification in the region's default language.
        Since a push notification can only be created by creating a translation in the default language, this is
        guaranteed to return a push notification translation.

        :return: The default translation of a push notification
        :rtype: ~integreat_cms.cms.models.push_notifications.push_notification_translation.PushNotificationTranslation
        """
        return self.translations.filter(language=self.region.default_language).first()

    @property
    def best_translation(self):
        """
        This function returns the translation of this push notification in the current backend language and if it
        doesn't exist, it provides a fallback to the translation in the region's default language.

        :return: The "best" translation of a push notification for displaying in the backend
        :rtype: ~integreat_cms.cms.models.push_notifications.push_notification_translation.PushNotificationTranslation
        """
        return (
            self.backend_translation
            or self.default_translation
            or self.translations.first()
        )

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``PushNotification object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the push notification
        :rtype: str
        """
        return self.best_translation.title

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<PushNotification: PushNotification object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the push notification
        :rtype: str
        """
        return f"<PushNotification (id: {self.id}, channel: {self.channel}, region: {self.region.slug})>"

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
