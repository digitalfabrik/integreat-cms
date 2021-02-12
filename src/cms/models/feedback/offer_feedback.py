from django.db import models
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback
from ..offers.offer import Offer
from ..regions.region import Region


class OfferFeedback(Feedback):
    """
    Database model representing feedback about offers.
    """

    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("offer"),
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="offer_feedback",
        verbose_name=_("region"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("offer feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("offer feedback")
        #: The default permissions for this model
        default_permissions = ()
