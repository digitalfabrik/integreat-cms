"""Model for Point of Interests

"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from .site import Site
from .language import Language


class POI(models.Model):
    """Object for Point of Interests

    Args:
        models : Databas model inherit from the standard django models
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    address = models.CharField(max_length=250)
    postcode = models.CharField(max_length=10)
    city = models.CharField(max_length=250)
    region = models.CharField(max_length=250)
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


class POITranslation(models.Model):
    """Translation of an Point of Interest

    Args:
        models : Databas model inherit from the standard django models
    """
    title = models.CharField(max_length=250)
    poi = models.ForeignKey(POI, related_name='poi_translations', null=True,
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
