"""Class defining event-related database models

Raises:
    ValidationError: Raised when an value does not match the requirements
"""
from datetime import datetime, time, date
from dateutil.rrule import weekday, rrule

from django.db import models

from .recurrence_rule import RecurrenceRule
from ..pois.poi import POI
from ..regions.region import Region
from ...constants import frequency


class Event(models.Model):
    """Database object representing an event with name, date and the option to add recurrency.

    Args:
        models : Database model inherit from the standard django models

    Raises:
        ValidationError: Raised if the recurrence end date is after the start date
        ValidationError: Raised if start or end date isn't null when the other one is
        ValidationError: Raised if the end date is before the start date
    """

    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    location = models.ForeignKey(POI, on_delete=models.PROTECT, null=True, blank=True)
    start_date = models.DateField()
    start_time = models.TimeField(blank=True)
    end_date = models.DateField()
    end_time = models.TimeField(blank=True)
    recurrence_rule = models.OneToOneField(RecurrenceRule, null=True, on_delete=models.SET_NULL)
    picture = models.ImageField(null=True, blank=True, upload_to='events/%Y/%m/%d')
    archived = models.BooleanField(default=False)

    @property
    def languages(self):
        event_translations = self.translations.prefetch_related('language').all()
        languages = []
        for event_translation in event_translations:
            languages.append(event_translation.language)
        return languages

    @property
    def is_recurring(self):
        return bool(self.recurrence_rule)

    @property
    def is_all_day(self):
        return self.start_time == time.min and self.end_time == time.max.replace(second=0, microsecond=0)

    def get_translation(self, language_code):
        return self.translations.filter(language__code=language_code).first()

    @classmethod
    def archived_count(cls, region_slug):
        return cls.objects.filter(region__slug=region_slug, archived=True).count()

    @classmethod
    def get_list(cls, region_slug, archived=False):
        """
        Function: Get List View

        Args:
            region_slug: slug of the region the event belongs to
            archived: whether or not archived pages should be returned

        Returns:
            [events]: Array of all Events
        """
        events = cls.objects.all().prefetch_related(
            'translations'
        ).filter(
            region__slug=region_slug,
            archived=archived
        )
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
        if recurrence is not None:
            until = min(end, datetime.combine(recurrence.recurrence_end_date
                                              if recurrence.recurrence_end_date
                                              else date.max, time.max))
            if recurrence.frequency in (frequency.DAILY, frequency.YEARLY):
                occurrences = rrule(recurrence.frequency,
                                    dtstart=event_start,
                                    interval=recurrence.interval,
                                    until=until)
            elif recurrence.frequency == frequency.WEEKLY:
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

    class Meta:
        ordering = ['start_date', 'start_time']
        default_permissions = ()
        permissions = (
            ('view_events', 'Can view events'),
            ('edit_events', 'Can edit events'),
            ('publish_events', 'Can publish events')
        )
