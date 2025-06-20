from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel


class PageAccesses(AbstractBaseModel):
    """
    Data model representing the accesses to a page.
    This is essentially a cache to alleviate pressure on the Matomo server
    and this table should be able to get wiped without actual data loss.
    """

    access_date = models.DateField(
        verbose_name="Date of the page accesses",
    )
    language = models.ForeignKey(
        "cms.Language",
        on_delete=models.CASCADE,
        verbose_name="Languages of the page that was accessed",
    )
    page = models.ForeignKey(
        "cms.Page",
        on_delete=models.CASCADE,
        verbose_name="Accessed page",
    )
    accesses = models.IntegerField(
        validators=[MinValueValidator(0)], verbose_name="Page accesses"
    )

    def __str__(self) -> str:
        return f"{self.page} - Accesses: {self.accesses}, language: {self.language}, date: {self.access_date}"

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<PageAccesses: PageAccesses object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the PageAccesses
        """
        return f"<PageAccesses (id: {self.id}, accesses: {self.accesses})>"

    class Meta:
        verbose_name = _("page accesses")
        default_related_name = "page_accesses"
        verbose_name_plural = _("page accesses")
        default_permissions = ("change", "delete", "view")
        ordering = ["pk"]

        constraints = [
            models.UniqueConstraint(
                fields=["page", "language", "access_date"],
                name="%(class)s_unique_version",
            ),
        ]
