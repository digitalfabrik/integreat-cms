"""Model for Point of Interests

"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from ..regions.region import Region


class POI(models.Model):
    """Object for Point of Interests

    Args:
        models : Databas model inherit from the standard django models
    """

    region = models.ForeignKey(Region, related_name='pois', on_delete=models.CASCADE)
    address = models.CharField(max_length=250)
    postcode = models.CharField(max_length=10)
    city = models.CharField(max_length=250)
    country = models.CharField(max_length=250)
    latitude = models.FloatField()
    longitude = models.FloatField()

    @classmethod
    def get_list_view(cls):
        """Provides List of all POIs in german

        Returns:
            [POI]: List of all german POIs
        """

        pois = cls.objects.all().prefetch_related(
            'translations'
        )

        return pois

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_pois', 'Can manage points of interest'),
        )

    @property
    def languages(self):
        poi_translations = self.translations.prefetch_related('language').all()
        languages = []
        for poi_translation in poi_translations:
            languages.append(poi_translation.language)
        return languages

    def get_translation(self, language_code):
        try:
            poi_translation = self.translations.get(language__code=language_code)
        except ObjectDoesNotExist:
            poi_translation = None
        return poi_translation
