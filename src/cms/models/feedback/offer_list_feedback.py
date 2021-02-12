from django.db import models
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback
from ..regions.region import Region


class OfferListFeedback(Feedback):
    """
    Database model representing feedback about the offer list (e.g. missing offers).
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="offer_list_feedback",
        verbose_name=_("region"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("offer list feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("offer list feedback")
        #: The default permissions for this model
        default_permissions = ()
