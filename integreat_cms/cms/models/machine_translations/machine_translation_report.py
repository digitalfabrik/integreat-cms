from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from ..regions.region import Region


class MachineTranslationReport(AbstractBaseModel):
    """
    A queued machine translation outcome report for one user, not yet seen by
    them - read destructively via :func:`~integreat_cms.cms.views.utils.machine_translation_report.get_machine_translation_report`.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="machine_translation_reports",
        verbose_name=_("user"),
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="machine_translation_reports",
        verbose_name=_("region"),
    )
    content_type = models.CharField(
        max_length=20,
        verbose_name=_("content type"),
    )
    language_slugs = models.JSONField(verbose_name=_("target language slugs"))
    results = models.JSONField(verbose_name=_("per-language, per-object results"))
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )

    def get_repr(self) -> str:
        """
        :return: The canonical string representation of this report
        """
        return (
            f"<MachineTranslationReport (id: {self.id}, user_id: {self.user_id}, "
            f"region_id: {self.region_id}, content_type: {self.content_type!r})>"
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("machine translation report")
        #: The plural verbose name of the model
        verbose_name_plural = _("machine translation reports")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["created_at"]
        #: The default permissions for this model
        default_permissions = ()
        #: Composite index matching the exact filter used to read a user's queued reports
        indexes = [models.Index(fields=["user", "region", "content_type"])]
