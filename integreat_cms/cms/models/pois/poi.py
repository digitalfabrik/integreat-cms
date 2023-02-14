from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from linkcheck.models import Link

from ..abstract_content_model import AbstractContentModel
from ..media.media_file import MediaFile
from ..pois.poi_translation import POITranslation
from ..poi_categories.poi_category import POICategory
from ..users.organization import Organization
from ...utils.translation_utils import gettext_many_lazy as __


def get_default_opening_hours():
    """
    Return the default opening hours

    :return: The default opening hours
    :rtype: list
    """
    return [{"allDay": False, "closed": True, "timeSlots": []} for _ in range(7)]


class POI(AbstractContentModel):
    """
    Data model representing a point of interest (POI). It contains all relevant data about its exact position, including
    coordinates.
    """

    address = models.CharField(
        max_length=250, verbose_name=_("street and house number")
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
    website = models.URLField(max_length=250, blank=True, verbose_name=_("website"))
    email = models.EmailField(
        blank=True,
        verbose_name=_("email address"),
    )
    phone_number = models.CharField(
        max_length=250, blank=True, verbose_name=_("phone number")
    )
    category = models.ForeignKey(
        POICategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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
    def fallback_translations_enabled(self):
        """
        Whether translations should be returned in the default language if they do not exist

        :return: Whether fallback translations are enabled
        :rtype: bool
        """
        return self.region.fallback_translations_enabled

    @staticmethod
    def get_translation_model():
        """
        Returns the translation model of this content model

        :return: The class of translations
        :rtype: type
        """
        return POITranslation

    def archive(self):
        """
        Archives the poi and removes all links of this poi from the linkchecker
        """
        self.archived = True
        self.save()

        # Delete related link objects as they are no longer required
        Link.objects.filter(poi_translation__poi=self).delete()

    def restore(self):
        """
        Restores the event and adds all links of this event back
        """
        self.archived = False
        self.save()

        # Restore related link objects
        for translation in self.translations.distinct("poi__pk", "language__pk"):
            # The post_save signal will create link objects from the content
            translation.save(update_timestamp=False)

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
