from django.db import models
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback
from ..regions.region import Region


class RegionFeedback(Feedback):
    """
    Database model representing feedback about regions in general.
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("region"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("region feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("region feedback")
        #: The default permissions for this model
        default_permissions = ()
