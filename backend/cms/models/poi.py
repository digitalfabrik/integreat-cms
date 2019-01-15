from django.contrib.auth.models import User
from django.db import models

from .site import Site
from .language import Language


class POI(models.Model):
    site = models.ForeignKey(Site)
    address = models.CharField(max_length=250)
    postcode = models.CharField(max_length=10)
    city = models.CharField(max_length=250)
    region = models.CharField(max_length=250)
    country = models.CharField(max_length=250)
    latitude = models.FloatField()
    longitude = models.FloatField()

    @classmethod
    def get_list_view(cls):
        poi_translations = POITranslation.objects.filter(
            language='de'
        ).select_related('user')
        pois = cls.objects.all().prefetch_related(
            models.Prefetch('poi_translations', queryset=poi_translations)
        ).filter(poi_translations__language='de')

        return pois


class POITranslation(models.Model):
    title = models.CharField(max_length=250)
    poi = models.ForeignKey(POI, related_name='poi_translations')
    permalink = models.CharField(max_length=60)
    STATUS = (
        ('draft', 'Entwurf'),
        ('in-review', 'Ausstehender Review'),
        ('reviewed', 'Review abgeschlossen'),
    )
    status = models.CharField(max_length=9, choices=STATUS, default='draft')
    description = models.TextField()
    language = models.ForeignKey(Language)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User)
