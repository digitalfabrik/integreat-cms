from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..regions.region import Region, Language
from ...constants import status


class POI(models.Model):
    """
    Data model representing a point of interest (POI). It contains all relevant data about its exact position, including
    coordinates.
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="pois",
        verbose_name=_("region"),
    )
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
    thumbnail = models.ImageField(
        null=True,
        blank=True,
        upload_to="pois/%Y/%m/%d",
        verbose_name=_("thumbnail icon"),
    )
    archived = models.BooleanField(
        default=False,
        verbose_name=_("archived"),
        help_text=_("Whether or not the location is read-only and hidden in the API."),
    )

    @property
    def languages(self):
        """
        This property returns a QuerySet of all :class:`~cms.models.languages.language.Language` objects, to which a POI
        translation exists.

        :return: QuerySet of all :class:`~cms.models.languages.language.Language` a POI is translated into
        :rtype: ~django.db.models.query.QuerySet [ ~cms.models.languages.language.Language ]
        """
        return Language.objects.filter(poi_translations__poi=self)

    def get_translation(self, language_code):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~cms.models.languages.language.Language` code.

        :param language_code: The code of the desired :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The POI translation in the requested :class:`~cms.models.languages.language.Language` or :obj:`None`
                 if no translation exists
        :rtype: ~cms.models.pois.poi_translation.POITranslation
        """
        return self.translations.filter(language__code=language_code).first()

    def get_public_translation(self, language_code):
        """
        This function retrieves the newest public translation of a POI.

        :param language_code: The code of the requested :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The public translation of a POI
        :rtype: ~cms.models.pois.poi_translation.POITranslation
        """
        return self.translations.filter(
            language__code=language_code,
            status=status.PUBLIC,
        ).first()

    class Meta:
        #: The verbose name of the model
        verbose_name = _("location")
        #: The plural verbose name of the model
        verbose_name_plural = _("locations")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (("manage_pois", "Can manage points of interest"),)
