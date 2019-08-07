"""Model for Point of Interests

"""
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils import timezone

from .region import Region
from .language import Language


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

        poi_translations = POITranslation.objects.filter(
            language='de'
        ).select_related('creator')
        pois = cls.objects.all().prefetch_related(
            models.Prefetch('poi_translations', queryset=poi_translations)
        ).filter(poi_translations__language='de')

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


class POITranslation(models.Model):
    """Translation of an Point of Interest

    Args:
        models : Databas model inherit from the standard django models
    """
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=200, blank=True)
    poi = models.ForeignKey(POI, related_name='translations', null=True,
                            on_delete=models.SET_NULL)
    permalink = models.CharField(max_length=60)
    STATUS = (
        ('draft', 'Entwurf'),
        ('in-review', 'Ausstehender Review'),
        ('reviewed', 'Review abgeschlossen'),
    )
    status = models.CharField(max_length=9, choices=STATUS, default='draft')
    description = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        default_permissions = ()
