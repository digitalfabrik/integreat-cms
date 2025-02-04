from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .feedback import Feedback

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class EventListFeedback(Feedback):
    """
    Database model representing feedback about the event list (e.g. missing events).
    """

    @property
    def object_name(self) -> str:
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        """
        return _("Event list")

    @cached_property
    def object_url(self) -> str:
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        """
        return reverse(
            "events",
            kwargs={
                "region_slug": self.region.slug,
            },
        )

    @property
    def related_feedback(self) -> QuerySet[EventListFeedback]:
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        """
        return EventListFeedback.objects.filter(
            region=self.region,
            language=self.language,
            is_technical=self.is_technical,
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event list feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("event list feedback")
        #: The default permissions for this model
        default_permissions = ()
