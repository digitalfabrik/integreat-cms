from django.contrib.auth.models import User
from django.db import models


class POI(models.Model):
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
        ('review', 'Ausstehender Review'),
        ('public', 'Veröffentlicht'),
    )
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    description = models.TextField()
    language = models.CharField(max_length=2)
    version = models.PositiveIntegerField(default=0)
    active_version = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User)
