from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..languages.language import Language
from ...constants import feedback_emotions


class Feedback(models.Model):
    """
    Database model representing feedback from app-users.
    """

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("language"),
    )
    #: Manage choices in :mod:`cms.constants.feedback_emotions`
    emotion = models.CharField(
        max_length=3,
        choices=feedback_emotions.CHOICES,
        verbose_name=_("emotion"),
        help_text=_("Whether the feedback is positive or negative"),
    )
    comment = models.CharField(max_length=1000, verbose_name=_("comment"))
    is_technical = models.BooleanField(
        verbose_name=_("technical"),
        help_text=_("Whether or not the feedback is targeted at the developers"),
    )
    read_status = models.BooleanField(
        default=False,
        verbose_name=_("read"),
        help_text=_("Whether or not the feedback is marked as read"),
    )

    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("feedback")
        #: The default permissions for this model
        default_permissions = ()
        #:  The custom permissions for this model
        permissions = (("view_feedback", "Can view feedback"),)
