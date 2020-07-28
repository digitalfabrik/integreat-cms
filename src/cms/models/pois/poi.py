from django.db import models

from ..regions.region import Region
from ...constants import status


class POI(models.Model):
    """
    Data model representing a point of interest (POI). It contains all relevant data about its exact position, including
    coordinates.

    :param id: The database id of the POI
    :param address: The street and house number of the POI
    :param postcode: The postal code of the POI
    :param city: The city in which the POI is located
    :param country: The country in which the POI is located
    :param latitude: The latitude coordinate of the POI
    :param longitude: The longitude coordinate of the POI
    :param archived: Whether or not the POI is archived (read-only and hidden in the API)

    Relationship fields:

    :param region: The region of the POI (related name: ``pois``)

    Reverse relationships:

    :param events: All events which take place at this location
    :param translations: All translations of this POI
    """

    region = models.ForeignKey(Region, related_name='pois', on_delete=models.CASCADE)
    address = models.CharField(max_length=250)
    postcode = models.CharField(max_length=10)
    city = models.CharField(max_length=250)
    country = models.CharField(max_length=250)
    latitude = models.FloatField()
    longitude = models.FloatField()
    archived = models.BooleanField(default=False)

    @classmethod
    def get_list(cls, region_slug, archived=False):
        """
        Get all POIs of one specific :class:`~cms.models.regions.region.Region` (either all archived or all not
        archived ones)

        :param region_slug: slug of the :class:`~cms.models.regions.region.Region` the POI belongs to
        :type region_slug: str

        :param archived: whether or not archived POIs should be returned, defaults to ``False``
        :type archived: bool, optional

        :return: A :class:`~django.db.models.query.QuerySet` of either archived or not archived POIs in the requested
                 :class:`~cms.models.regions.region.Region`
        :rtype: ~django.db.models.query.QuerySet
        """

        return cls.objects.all().prefetch_related(
            'translations'
        ).filter(
            region__slug=region_slug,
            archived=archived
        )

    @property
    def languages(self):
        """
        This property returns a list of all :class:`~cms.models.languages.language.Language` objects, to which a POI
        translation exists.

        :return: list of all :class:`~cms.models.languages.language.Language` a POI is translated into
        :rtype: list [ ~cms.models.languages.language.Language ]
        """
        poi_translations = self.translations.prefetch_related('language').all()
        languages = []
        for poi_translation in poi_translations:
            languages.append(poi_translation.language)
        return languages

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
        return self.translations.filter(
            language__code=language_code
        ).first()

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
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple

        :param permissions: The custom permissions for this model
        :type permissions: tuple
        """
        default_permissions = ()
        permissions = (
            ('manage_pois', 'Can manage points of interest'),
        )
