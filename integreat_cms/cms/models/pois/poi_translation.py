from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link

if TYPE_CHECKING:
    from typing import Any, Literal

    from django.db.models import QuerySet

    from .. import POI, Region

from ...constants import status
from ...utils.translation_utils import gettext_many_lazy as __
from ..abstract_content_translation import AbstractContentTranslation
from ..decorators import modify_fields
from ..utils import format_object_translation


@modify_fields(
    slug={"verbose_name": _("link to the location")},
    title={"verbose_name": _("name of the location")},
    content={"verbose_name": _("description")},
)
class POITranslation(AbstractContentTranslation):
    """
    Data model representing a POI translation
    """

    poi = models.ForeignKey(
        "cms.POI",
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("location"),
    )
    meta_description = models.CharField(
        max_length=2048,
        blank=True,
        verbose_name=_("meta description"),
        help_text=__(
            _("Describe the location in one or two short sentences."),
            _(
                "This text will be displayed in the Google search results below the title.",
            ),
        ),
    )
    links = GenericRelation(Link, related_query_name="poi_translation")

    @cached_property
    def foreign_object(self) -> POI:
        """
        This property is an alias of the POI foreign key and is needed to generalize the :mod:`~integreat_cms.cms.utils.slug_utils`
        for all content types

        :return: The POI to which the translation belongs
        """
        return self.poi

    @staticmethod
    def foreign_field() -> Literal["poi"]:
        """
        Returns the string "poi" which ist the field name of the reference to the poi which the translation belongs to

        :return: The foreign field name
        """
        return "poi"

    @cached_property
    def url_infix(self) -> str:
        """
        Generates the infix of the url of the poi translation object

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: The infix of the url
        """
        return "locations"

    @cached_property
    def backend_edit_link(self) -> str:
        """
        This function returns the absolute url to the editor for this translation

        :return: The url
        """
        return reverse(
            "edit_poi",
            kwargs={
                "poi_id": self.poi.id,
                "language_slug": self.language.slug,
                "region_slug": self.poi.region.slug,
            },
        )

    @cached_property
    def map_url(self) -> str:
        """
        :return: the link to the POI on the Integreat map (if it exists), to google maps otherwise
        """
        if self.poi.location_on_map and self.status != status.DRAFT:
            return f"{settings.WEBAPP_URL}{self.get_absolute_url()}"
        return f"https://www.google.com/maps/search/?api=1&query={self.poi.address},{self.poi.city},{self.poi.country}"

    @staticmethod
    def default_icon() -> str | None:
        """
        :return: The default icon that should be used for this content translation type, or ``None`` for no icon
        """
        return "pin"

    @classmethod
    def search(cls, region: Region, language_slug: str, query: str) -> QuerySet:
        """
        Searches for all content translations which match the given `query` in their title or slug.
        :param region: The current region
        :param language_slug: The language slug
        :param query: The query string used for filtering the content translations
        :return: A query for all matching objects
        """
        queryset = super().search(region, language_slug, query)

        if region.fallback_translations_enabled:
            default_language_queryset = (
                super()
                .search(region, region.default_language.slug, query)
                .exclude(poi__translations__language__slug=language_slug)
            )
            queryset = cls.objects.filter(
                Q(id__in=queryset) | Q(id__in=default_language_queryset),
            )

        return queryset

    @classmethod
    def suggest(cls, **kwargs: Any) -> list[dict[str, Any]]:
        r"""
        Suggests keywords for POI search

        :param \**kwargs: The supplied kwargs
        :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}
        """
        results: list[dict[str, Any]] = []

        region = kwargs["region"]
        query = kwargs["query"]
        archived_flag = kwargs["archived_flag"]
        language_slug = kwargs["language_slug"]

        poi_translations = (
            cls.search(region, language_slug, query)
            .filter(poi__archived=archived_flag, status=status.PUBLIC)
            .select_related("poi__region", "language")
        )
        results.extend(
            format_object_translation(obj, "poi", language_slug)
            for obj in poi_translations
        )

        return results

    class Meta:
        #: The verbose name of the model
        verbose_name = _("location translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("location translations")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "poi_translations"
        #: The default permissions for this model
        default_permissions = ()
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["poi__pk", "language__pk", "-version"]
        #: A list of database constraints for this model
        constraints = [
            models.UniqueConstraint(
                fields=["poi", "language", "version"],
                name="%(class)s_unique_version",
            ),
        ]
