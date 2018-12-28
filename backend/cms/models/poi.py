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

    def __str__(self):
        return self.poi_translations.filter(poi_id=self.id, language='de').first().name

    def get_translations(self):
        return self.poi_translations

    @classmethod
    def get_list_view(cls):
        poi_translations = POITranslation.objects.filter(
            language='de'
        ).select_related('user')
        pois = cls.objects.all().prefetch_related(models.Prefetch(
            'poi_translations',
            queryset=poi_translations)
        ).filter(poi_translations__language='de')

        return pois


class POITranslation(models.Model):
    STATUS = (
        ('draft', 'Entwurf'),
        ('review', 'Ausstehender Review'),
        ('public', 'Veröffentlicht'),
    )
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    name = models.CharField(max_length=250)
    description = models.TextField()
    permalink = models.CharField(max_length=60)
    language = models.CharField(max_length=2)
    version = models.PositiveIntegerField(default=0)
    active_version = models.BooleanField(default=False)
    poi = models.ForeignKey(POI, related_name='poi_translations')
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User)
