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
    Data model representing the stored condition of a region

    Computing these metrics is too slow to do on request. They are computed every night (see
    :func:`~integreat_cms.cms.utils.region_condition_utils.update_region_conditions`) and stored
    here, at most one row per active or hidden region, overwritten whenever the computation of
    that region succeeds. Rows of regions which are no longer active or hidden are removed.
    ``computed_at`` tells how old the values are: a region whose computation failed or was not
    reached keeps the values of its last successful run.
    """

    #: The names of the metric fields. Each one must also match a ``dehydrate_<name>`` method of
    #: :class:`~integreat_cms.cms.views.region_condition.region_condition_actions.RegionConditionResource`,
    #: which computes it.
    METRICS: Final[tuple[str, ...]] = (
        "num_broken_links",
        "num_low_hix_pages",
        "num_pages",
        "num_pages_with_missing_or_outdated_translation",
        "num_outdated_pages",
        "num_languages_besides_root_language",
    )

    region = models.OneToOneField(
        Region,
        on_delete=models.CASCADE,
        related_name="condition",
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
