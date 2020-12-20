from django.db import models
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback
from ..events.event_translation import EventTranslation


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

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("event feedback")
        #: The default permissions for this model
        default_permissions = ()
