from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ..events.event_translation import EventTranslation
from .feedback import Feedback

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


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
    def object_name(self) -> str:
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        """
        return self.best_event_translation.title

    @cached_property
    def object_url(self) -> str:
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
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
    def best_event_translation(self) -> EventTranslation:
        """
        This property returns the best translation for the event this feedback comments on.

        :return: The best event translation
        """
        return self.event_translation.event.best_translation

    @property
    def related_feedback(self) -> QuerySet[EventFeedback]:
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
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
