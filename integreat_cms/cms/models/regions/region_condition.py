from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from .region import Region

if TYPE_CHECKING:
    from typing import Final


class RegionCondition(AbstractBaseModel):
    """
    Data model representing the condition of a region at the time it was computed

    Every nightly run of
    :func:`~integreat_cms.cms.utils.region_condition_utils.update_region_conditions` adds a row
    per region, the newest one is the current condition.
    """

    #: The metric fields, each computed by the ``dehydrate_<name>`` method of
    #: :class:`~integreat_cms.cms.views.region_condition.region_condition_actions.RegionConditionResource`
    METRICS: Final[tuple[str, ...]] = (
        "num_broken_links",
        "num_low_hix_pages",
        "num_pages",
        "num_pages_with_missing_or_outdated_translation",
        "num_outdated_pages",
        "num_languages_besides_root_language",
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="conditions",
        verbose_name=_("region"),
    )
    computed_at = models.DateTimeField(verbose_name=_("computed at"))
    num_broken_links = models.PositiveIntegerField(
        verbose_name=_("number of broken links"),
    )
    #: Counts page translations, not pages; the name matches the column of the region condition
    #: export
    num_low_hix_pages = models.PositiveIntegerField(
        verbose_name=_("number of page translations with low HIX value"),
    )
    num_pages = models.PositiveIntegerField(verbose_name=_("number of pages"))
    num_pages_with_missing_or_outdated_translation = models.PositiveIntegerField(
        verbose_name=_(
            "number of pages with at least one missing or outdated translation",
        ),
    )
    num_outdated_pages = models.PositiveIntegerField(
        verbose_name=_("number of outdated pages"),
    )
    num_languages_besides_root_language = models.PositiveIntegerField(
        verbose_name=_("number of active languages besides default language"),
    )

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which
        would return ``RegionCondition object (id)``.

        :return: A readable string representation of the region condition
        """
        return f"{self.region} ({self.computed_at:%Y-%m-%d %H:%M})"

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return
        ``<RegionCondition: RegionCondition object (id)>``.

        :return: The canonical string representation of the region condition
        """
        return f"<RegionCondition (id: {self.id}, region: {self.region.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("region condition")
        #: The plural verbose name of the model
        verbose_name_plural = _("region conditions")
        #: The default permissions for this model
        default_permissions = ()
        #: The newest condition first
        ordering = ["-computed_at"]
        indexes = [
            models.Index(
                fields=["region", "-computed_at"],
                name="regioncondition_newest",
            ),
        ]
