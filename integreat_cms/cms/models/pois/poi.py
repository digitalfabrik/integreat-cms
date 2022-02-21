from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..abstract_content_model import AbstractContentModel
from ..media.media_file import MediaFile
from ..pois.poi_translation import POITranslation


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
        verbose_name=_("latitude"), help_text=_("The latitude coordinate")
    )
    longitude = models.FloatField(
        verbose_name=_("longitude"), help_text=_("The longitude coordinate")
    )
    location_not_on_map = models.BooleanField(
        default=False,
        verbose_name=_("Do not show this location on map"),
        help_text=_("Tick if you do not show this location on map"),
    )
    icon = models.ForeignKey(
        MediaFile,
        verbose_name=_("icon"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    archived = models.BooleanField(
        default=False,
        verbose_name=_("archived"),
        help_text=_("Whether or not the location is read-only and hidden in the API."),
    )

    @staticmethod
    def get_translation_model():
        """
        Returns the translation model of this content model

        :return: The class of translations
        :rtype: type
        """
        return POITranslation

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
