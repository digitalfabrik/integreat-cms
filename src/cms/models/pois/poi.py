from django.db import models
from django.utils.translation import get_language, ugettext_lazy as _

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
    icon = models.ImageField(
        null=True,
        blank=True,
        upload_to="pois/%Y/%m/%d",
        verbose_name=_("icon"),
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

    def get_translation(self, language_slug):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~cms.models.languages.language.Language` slug.

        :param language_slug: The slug of the desired :class:`~cms.models.languages.language.Language`
        :type language_slug: str

        :return: The POI translation in the requested :class:`~cms.models.languages.language.Language` or :obj:`None`
                 if no translation exists
        :rtype: ~cms.models.pois.poi_translation.POITranslation
        """
        return self.translations.filter(language__slug=language_slug).first()

    def get_public_translation(self, language_slug):
        """
        This function retrieves the newest public translation of a POI.

        :param language_slug: The slug of the requested :class:`~cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of a POI
        :rtype: ~cms.models.pois.poi_translation.POITranslation
        """
        return self.translations.filter(
            language__slug=language_slug,
            status=status.PUBLIC,
        ).first()

    @property
    def backend_translation(self):
        """
        This function returns the translation of this POI in the current backend language.

        :return: The backend translation of a POI
        :rtype: ~cms.models.pois.poi_translation.POITranslation
        """
        return self.translations.filter(language__slug=get_language()).first()

    @property
    def default_translation(self):
        """
        This function returns the translation of this POI in the region's default language.
        Since a POI can only be created by creating a translation in the default language, this is guaranteed to return
        a POI translation.

        :return: The default translation of a POI
        :rtype: ~cms.models.pois.poi_translation.POITranslation
        """
        return self.translations.filter(language=self.region.default_language).first()

    @property
    def best_translation(self):
        """
        This function returns the translation of this POI in the current backend language and if it doesn't exist, it
        provides a fallback to the translation in the region's default language.

        :return: The "best" translation of a POI for displaying in the backend
        :rtype: ~cms.models.pois.poi_translation.POITranslation
        """
        return self.backend_translation or self.default_translation

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``POI object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the POI
        :rtype: str
        """
        return self.best_translation.title

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<POI: POI object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the POI
        :rtype: str
        """
        return f"<POI (id: {self.id}, region: {self.region.slug}, slug: {self.best_translation.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("location")
        #: The plural verbose name of the model
        verbose_name_plural = _("locations")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (("manage_pois", "Can manage points of interest"),)
