from django.db import models
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback
from ..pages.page_translation import PageTranslation


class PageFeedback(Feedback):
    """
    Database model representing feedback about pages.
    """

    page_translation = models.ForeignKey(
        PageTranslation,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("page translation"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("page feedback")
        #: The default permissions for this model
        default_permissions = ()
