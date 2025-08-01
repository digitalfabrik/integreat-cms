from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.functional import cached_property

from integreat_cms.cms.models.utils import get_default_opening_hours

if TYPE_CHECKING:
    from django.db.models.base import ModelBase


from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link

from ...utils.translation_utils import gettext_many_lazy as __
from ..abstract_content_model import AbstractContentModel
from ..media.media_file import MediaFile
from ..poi_categories.poi_category import POICategory
from ..pois.poi_translation import POITranslation
from ..users.organization import Organization

logger = logging.getLogger(__name__)


class POI(AbstractContentModel):
    """
    Data model representing a point of interest (POI). It contains all relevant data about its exact position, including
    coordinates.
    """

    address = models.CharField(
        max_length=250,
        verbose_name=_("street and house number"),
    )
    postcode = models.CharField(max_length=10, verbose_name=_("postal code"))
    city = models.CharField(max_length=250, verbose_name=_("city"))
    country = models.CharField(max_length=250, verbose_name=_("country"))
    latitude = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("latitude"),
        help_text=_("The latitude coordinate"),
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("longitude"),
        help_text=_("The longitude coordinate"),
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )
    location_on_map = models.BooleanField(
        default=False,
        verbose_name=_("Show this location on map"),
        help_text=_("Tick if you want to show this location on map"),
    )
    icon = models.ForeignKey(
        MediaFile,
        verbose_name=_("icon"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The best results are achieved with images in 16:9 aspect ratio."),
    )
    archived = models.BooleanField(
        default=False,
        verbose_name=_("archived"),
        help_text=_("Whether or not the location is read-only and hidden in the API."),
    )
    category = models.ForeignKey(
        POICategory,
        on_delete=models.PROTECT,
        related_name="pois",
        verbose_name=_("category"),
    )
    temporarily_closed = models.BooleanField(
        default=False,
        verbose_name=_("temporarily closed"),
        help_text=__(
            _("Whether or not the location is temporarily closed."),
            _("The opening hours remain and are only hidden."),
        ),
    )
    appointment_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_("appointment link"),
        help_text=_(
            "Link to an external website where an appointment for this location can be made.",
        ),
    )
    opening_hours = models.JSONField(
        default=get_default_opening_hours,
        verbose_name=_("opening hours"),
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pois",
        verbose_name=_("organization"),
        help_text=_("Specify which organization operates this location."),
    )
    barrier_free = models.BooleanField(
        null=True,
        default=None,
        verbose_name=_("barrier free"),
        help_text=_("Indicate if the location is barrier free."),
    )

    @property
    def fallback_translations_enabled(self) -> bool:
        """
        Whether translations should be returned in the default language if they do not exist

        :return: Whether fallback translations are enabled
        """
        return self.region.fallback_translations_enabled

    @staticmethod
    def get_translation_model() -> ModelBase:
        """
        Returns the translation model of this content model

        :return: The class of translations
        """
        return POITranslation

    def can_be_deleted(self) -> tuple[bool, str | None]:
        """
        Checks if poi can be deleted
        """
        if self.is_used:
            return False, _("a poi used by an event or a contact cannot be deleted.")
        return True, None

    def archive(self) -> bool:
        """
        Archives the poi and removes all links of this poi from the linkchecker
        """
        was_successful = False
        if not self.is_currently_used:
            self.archived = True
            self.save()
            # Delete related link objects as they are no longer required
            Link.objects.filter(poi_translation__poi=self).delete()
            was_successful = True
        else:
            logger.debug(
                "Can't be archived because this poi is used by a contact or an upcoming event",
            )
        return was_successful

    def restore(self) -> None:
        """
        Restores the poi and adds all links of this poi back
        """
        self.archived = False
        self.save()

        # Restore related link objects
        for translation in self.translations.distinct("poi__pk", "language__pk"):
            # The post_save signal will create link objects from the content
            translation.save(update_timestamp=False)

    @property
    def is_used(self) -> bool:
        """
        :return: whether this poi is used by another model
        """
        return self.events.exists() or self.contacts.exists()

    @property
    def is_currently_used(self) -> bool:
        """
        :return: whether this poi is used by a contact or an upcoming event
        """
        upcoming_events = self.events.filter_upcoming()
        return self.contacts.exists() or upcoming_events.exists()

    @cached_property
    def short_address(self) -> str:
        """
        :return: one-line representation of this POI's address
        """
        return f"{self.address}, {self.postcode} {self.city}"

    @cached_property
    def map_url(self) -> str:
        """
        :return: the link to the POI of the default (public) translation
        """
        return (
            self.default_public_translation.map_url
            if self.default_public_translation
            else self.default_translation.map_url
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("location")
        #: The plural verbose name of the model
        verbose_name_plural = _("locations")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "pois"
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["pk"]
