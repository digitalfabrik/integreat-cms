from django.db import models
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback
from ..regions.region import Region


class EventListFeedback(Feedback):
    """
    Database model representing feedback about the event list (e.g. missing events).
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="event_list_feedback",
        verbose_name=_("region"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event list feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("event list feedback")
        #: The default permissions for this model
        default_permissions = ()
