from __future__ import annotations

from typing import TYPE_CHECKING

import pgtrigger
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link

from integreat_cms.cms.utils.slug_utils import generate_unique_slug

if TYPE_CHECKING:
    from typing import Any, Literal

    from django.db.models import QuerySet

    from integreat_cms.cms.utils.slug_utils import SlugKwargs

    from .. import Place, Region

from ...constants import status
from ...utils.translation_utils import gettext_many_lazy as __
from ..abstract_content_translation import AbstractContentTranslation
from ..decorators import modify_fields
from ..utils import format_object_translation


@modify_fields(
    slug={"verbose_name": _("link to the place")},
    title={"verbose_name": _("name of the place")},
    content={"verbose_name": _("description")},
)
class PlaceTranslation(AbstractContentTranslation):
    """
    Data model representing a Place translation
    """

    place = models.ForeignKey(
        "cms.Place",
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("place"),
    )
    meta_description = models.CharField(
        max_length=2048,
        blank=True,
        verbose_name=_("meta description"),
        help_text=__(
            _("Describe the place in one or two short sentences."),
            _(
                "This text will be displayed in the Google search results below the title.",
            ),
        ),
    )
    links = GenericRelation(Link, related_query_name="place_translation")

    @cached_property
    def foreign_object(self) -> Place:
        """
        This property is an alias of the Place foreign key and is needed to generalize the :mod:`~integreat_cms.cms.utils.slug_utils`
        for all content types

        :return: The Place to which the translation belongs
        """
        return self.place

    @staticmethod
    def foreign_field() -> Literal["place"]:
        """
        Returns the string "place" which ist the field name of the reference to the place which the translation belongs to

        :return: The foreign field name
        """
        return "place"

    @cached_property
    def url_infix(self) -> str:
        """
        Generates the infix of the url of the place translation object

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: The infix of the url
        """
        # The published URLs of the web app are part of the public interface and stay as they are
        return "locations"

    @cached_property
    def backend_edit_link(self) -> str:
        """
        This function returns the absolute url to the editor for this translation

        :return: The url
        """
        return reverse(
            "edit_place",
            kwargs={
                "place_id": self.place.id,
                "language_slug": self.language.slug,
                "region_slug": self.place.region.slug,
            },
        )

    @cached_property
    def map_url(self) -> str:
        """
        :return: the link to the Place on the Integreat map (if it exists), to google maps otherwise
        """
        if self.place.place_on_map and self.status != status.DRAFT:
            return f"{settings.WEBAPP_URL}{self.get_absolute_url()}"
        return f"https://www.google.com/maps/search/?api=1&query={self.place.address},{self.place.city},{self.place.country}"

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
                .exclude(place__translations__language__slug=language_slug)
            )
            queryset = cls.objects.filter(
                Q(id__in=queryset) | Q(id__in=default_language_queryset),
            )

        return queryset

    @classmethod
    def suggest(cls, **kwargs: Any) -> list[dict[str, Any]]:
        r"""
        Suggests keywords for Place search

        :param \**kwargs: The supplied kwargs
        :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}
        """
        results: list[dict[str, Any]] = []

        region = kwargs["region"]
        query = kwargs["query"]
        archived_flag = kwargs["archived_flag"]
        language_slug = kwargs["language_slug"]
        link_suggestion_flag = kwargs["link_suggestion_flag"]

        place_translations = (
            cls.search(region, language_slug, query)
            .filter(place__archived=archived_flag, status=status.PUBLIC)
            .select_related("place__region", "language")
        )

        if not link_suggestion_flag:
            place_translations = place_translations.order_by("title").distinct("title")

        results.extend(
            format_object_translation(obj, "place", language_slug)
            for obj in place_translations
        )

        return results

    def clean(self) -> None:
        """
        Checks if the slug is unique and generates when necessary
        """
        if not getattr(self, "is_validated", False):
            kwargs: SlugKwargs = {
                "slug": self.slug,
                "manager": type(self).objects,
                "object_instance": self,
                "foreign_model": "place",
                "region": self.place.region,
                "language": self.language,
                "fallback": self.title,
            }
            self.slug = generate_unique_slug(**kwargs)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save to perform unique slug validation
        """
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        #: The verbose name of the model
        verbose_name = _("place translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("place translations")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "place_translations"
        #: The default permissions for this model
        default_permissions = ()
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["place__pk", "language__pk", "-version"]
        #: A list of database constraints for this model
        constraints = [
            models.UniqueConstraint(
                fields=["place", "language", "version"],
                name="%(class)s_unique_version",
            ),
            models.CheckConstraint(
                condition=Q(slug=Lower("slug")), name="%(class)s_slug_lowercase"
            ),
        ]
        triggers = [
            # Trigger for INSERT and UPDATE
            pgtrigger.Trigger(
                name="enforce_slug_uniqueness",
                when=pgtrigger.Before,
                operation=pgtrigger.Insert | pgtrigger.Update,
                func="""
                DECLARE
                    new_region_id INTEGER;
                BEGIN
                    -- Look up the region for the new/updated place
                    SELECT region_id INTO new_region_id
                    FROM cms_place
                    WHERE id = NEW.place_id;

                    -- Set advisory lock (Postgresql specific)
                    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.language_id || ':' || new_region_id || ':' || NEW.slug, 0));

                    -- Check if there's a conflict (same slug/language/region but different place)
                    IF EXISTS (
                        SELECT 1
                        FROM cms_placetranslation t
                        JOIN cms_place p ON t.place_id = p.id
                        WHERE t.slug = NEW.slug
                        AND t.language_id = NEW.language_id
                        AND p.region_id = new_region_id
                        AND t.place_id <> NEW.place_id
                    ) THEN
                        RAISE EXCEPTION 'Slug must be unique per language and region across different places.' USING ERRCODE = 'unique_violation'; -- SQLSTATE 23505
                    END IF;

                    RETURN NEW;
                END;
                """,
            ),
        ]
