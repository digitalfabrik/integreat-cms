from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ..events.event_translation import EventTranslation
from .feedback import Feedback


class EventFeedback(Feedback):
    """
    Database model representing feedback about events.
    """

    event_translation = models.ForeignKey(
        EventTranslation,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("event translation"),
    )

    @property
    def object_name(self):
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        :rtype: str
        """
        return self.best_event_translation.title

    @cached_property
    def object_url(self):
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        :rtype: str
        """
        return reverse(
            "edit_event",
            kwargs={
                "event_id": self.event_translation.event.id,
                "region_slug": self.region.slug,
                "language_slug": self.best_event_translation.language.slug,
            },
        )

    @cached_property
    def best_event_translation(self):
        """
        This property returns the best translation for the event this feedback comments on.

        :return: The best event translation
        :rtype: ~integreat_cms.cms.models.events.event_translation.EventTranslation
        """
        return self.event_translation.event.best_translation

    @property
    def related_feedback(self):
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.feedback.event_feedback.EventFeedback ]
        """
        return EventFeedback.objects.filter(
            event_translation__event=self.event_translation.event,
            language=self.language,
            is_technical=self.is_technical,
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("event feedback")
        #: The default permissions for this model
        default_permissions = ()
