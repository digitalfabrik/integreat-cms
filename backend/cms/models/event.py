"""Class defining event-related database models

Raises:
    ValidationError: Raised when an value does not match the requirements
"""
from datetime import datetime, time, date

from dateutil.rrule import weekday, rrule
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from .site import Site
from .language import Language
from .poi import POI


class RecurrenceRule(models.Model):
    """
    Object to define the recurrence frequency
    Args:
        models ([type]): [description]
    Raises:
        ValidationError: Error raised when weekdays_for_weekly does not fit into the range
        from 0 to 6 or when the value of weekdays_for_monthly isn't between -5 and 5.
    """

    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'
    MONTHLY = 'MONTHLY'
    YEARLY = 'YEARLY'

    FREQUENCY = (
        (DAILY, 'Täglich'),
        (WEEKLY, 'Wöchentlich'),
        (MONTHLY, 'Monatlich'),
        (YEARLY, 'Jährlich')
    )
    frequency = models.CharField(max_length=7, choices=FREQUENCY)
    interval = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    weekdays_for_weekly = ArrayField(
        models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)]),
        null=True)
    weekday_for_monthly = models.IntegerField(null=True)
    week_for_monthly = models.IntegerField(
        null=True,
        validators=[MinValueValidator(-5), MaxValueValidator(5)]
    )
    end_date = models.DateField(null=True, default=None)

    def clean(self):
        if self.frequency == RecurrenceRule.WEEKLY \
                and (self.weekdays_for_weekly is None or self.weekdays_for_weekly.size() == 0):
            raise ValidationError('No weekdays selected for weekly recurrence')
        if self.frequency == 'monthly' and (
                self.weekday_for_monthly is None or self.week_for_monthly is None):
            raise ValidationError('No weekday or no week selected for monthly recurrence')


class Event(models.Model):
    """Database object representing an event with name, date and the option to add recurrency.

    Args:
        models : Databas model inherit from the standard django models

    Raises:
        ValidationError: Raised if the recurrence end date is after the start date
        ValidationError: Raised if start or end date isn't null when the other one is
        ValidationError: Raised if the end date is before the start date
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    location = models.ForeignKey(POI, on_delete=models.PROTECT, null=True, blank=True)
    start_date = models.DateField()
    start_time = models.TimeField(null=True)
    end_date = models.DateField()
    end_time = models.TimeField(null=True)
    recurrence_rule = models.OneToOneField(RecurrenceRule, null=True, on_delete=models.SET_NULL)
    picture = models.ImageField(null=True, blank=True, upload_to='events/%Y/%m/%d')

    def clean(self):
        if self.recurrence_rule:
            if self.recurrence_rule.end_date <= self.start_date:
                raise ValidationError('recurrence end date must be after the start date!')
        if self.start_time is None ^ self.end_time is None:
            raise ValidationError(
                'start_time and end_time must either be both null or both non-null')
        if self.end_date < self.start_date or (
                self.end_date == self.start_date and self.end_time < self.start_time):
            raise ValidationError('end datetime mustn\'t be before start datetime')

    def __str__(self):
        return self.event_translations.filter(event_id=self.id, language='de').first().title

    def get_translations(self):
        """Provides all translations of the Event
        Returns:
            [event_translations]: Array with all translations related to this event
        """

        return self.event_translations.all()

    @classmethod
    def get_list_view(cls):
        """
        Function: Get List View
        Returns:
            [events]: Array of all Events
        """

        event_translations = EventTranslation.objects.filter(
            language='de'
        ).select_related('creator')
        events = cls.objects.all().prefetch_related(
            models.Prefetch('event_translations', queryset=event_translations)
        ).filter(event_translations__language='de')
        return events

    def get_occurrences(self, start, end):
        """
        Returns start datetimes of occurrences of the event that overlap with [start, end]
        Expects start < end
        :type start: datetime
        :type end: datetime
        :return:
        """
        event_start = datetime.combine(self.start_date,
                                       self.start_time if self.start_time else time.min)
        event_end = datetime.combine(self.end_date, self.end_time if self.end_time else time.max)
        event_span = event_end - event_start
        recurrence = self.recurrence_rule
        if recurrence:
            until = min(end, datetime.combine(recurrence.end_date
                                              if recurrence.end_date
                                              else date.max, time.max))
            if recurrence.frequency in (RecurrenceRule.DAILY, RecurrenceRule.YEARLY):
                occurrences = rrule(recurrence.frequency,
                                    dtstart=event_start,
                                    interval=recurrence.interval,
                                    until=until)
            elif recurrence.frequency == RecurrenceRule.WEEKLY:
                occurrences = rrule(recurrence.frequency,
                                    dtstart=event_start,
                                    interval=recurrence.interval,
                                    byweekday=recurrence.weekdays_for_weekly,
                                    until=until)
            else:
                occurrences = rrule(recurrence.frequency,
                                    dtstart=event_start,
                                    interval=recurrence.interval,
                                    byweekday=weekday(recurrence.weekday_for_monthly,
                                                      recurrence.week_for_monthly),
                                    until=until)
            return [x for x in occurrences if start <= x <= end or start <= x + event_span <= end]
        return [event_start] if start <= event_start <= end or start <= event_end <= end else []


class EventTranslation(models.Model):
    """
    Database object representing an event tranlsation
    """
    STATUS = (
        ('draft', 'Entwurf'),
        ('in-review', 'Ausstehender Review'),
        ('reviewed', 'Review abgeschlossen'),
    )
    status = models.CharField(max_length=9, choices=STATUS, default='draft')
    title = models.CharField(max_length=250)
    description = models.TextField()
    permalink = models.CharField(max_length=60)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    event = models.ForeignKey(Event, related_name='event_translations', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
