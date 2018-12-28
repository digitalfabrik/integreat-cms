from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from cms.models import Site
from cms.models.poi import POI


class Event(models.Model):
    site = models.ForeignKey(Site)
    location = models.ForeignKey(POI, on_delete=models.PROTECT, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    picture = models.ImageField(null=True, blank=True, upload_to='events/%Y/%m/%d')
    is_all_day = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    has_recurring_end_date = models.BooleanField(default=False)
    recurring_end_date = models.DateField(null=True, default=None, blank=True)
    FREQUENCY = (
        ('daily', 'Täglich'),
        ('weekly', 'Wöchentlich'),
        ('monthly', 'Monatlich'),
        ('yearly', 'Jährlich')
    )
    frequency = models.CharField(max_length=7, choices=FREQUENCY,
                                 null=True, blank=True, default=None)

    def clean(self):
        if self.recurring_end_date:
            if self.recurring_end_date <= self.start_date.date():
                raise ValidationError('Wiederholungsenddatum liegt nicht nach dem Startdatum!')
        if self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError('Enddatum liegt nicht nach dem Startdatum!')

    def __str__(self):
        return self.event_translations.filter(event_id=self.id, language='de').first().title

    def get_translations(self):
        return self.event_translations.all()

    @classmethod
    def get_list_view(cls):
        event_translations = EventTranslation.objects.filter(
            language='de'
        ).select_related('user')
        events = cls.objects.all().prefetch_related(
            models.Prefetch('event_translations', queryset=event_translations)
        ).filter(event_translations__language='de')
        return events


class EventTranslation(models.Model):
    STATUS = (
        ('draft', 'Entwurf'),
        ('review', 'Ausstehender Review'),
        ('public', 'Veröffentlicht'),
    )
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    title = models.CharField(max_length=250)
    description = models.TextField()
    permalink = models.CharField(max_length=60)
    language = models.CharField(max_length=2)
    version = models.PositiveIntegerField(default=0)
    active_version = models.BooleanField(default=False)
    event = models.ForeignKey(to='Event', related_name='event_translations')
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User)
