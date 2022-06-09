from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from linkcheck.models import Link

from ..abstract_content_translation import AbstractContentTranslation
from ..decorators import modify_fields


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
    short_description = models.CharField(
        max_length=2048, verbose_name=_("short description")
    )
    links = GenericRelation(Link, related_query_name="poi_translation")

    @cached_property
    def foreign_object(self):
        """
        This property is an alias of the POI foreign key and is needed to generalize the :mod:`~integreat_cms.cms.utils.slug_utils`
        for all content types

        :return: The POI to which the translation belongs
        :rtype: ~integreat_cms.cms.models.pois.poi.POI
        """
        return self.poi

    @staticmethod
    def foreign_field():
        """
        Returns the string "poi" which ist the field name of the reference to the poi which the translation belongs to

        :return: The foreign field name
        :rtype: str
        """
        return "poi"

    @cached_property
    def url_infix(self):
        """
        Generates the infix of the url of the poi translation object

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: The infix of the url
        :rtype: str
        """
        return "locations"

    @cached_property
    def backend_edit_link(self):
        """
        This function returns the absolute url to the editor for this translation

        :return: The url
        :rtype: str
        """
        return reverse(
            "edit_poi",
            kwargs={
                "poi_id": self.poi.id,
                "language_slug": self.language.slug,
                "region_slug": self.poi.region.slug,
            },
        )

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
