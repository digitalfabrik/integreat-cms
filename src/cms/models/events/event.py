from datetime import datetime, time, date
from dateutil.rrule import weekday, rrule

from django.db import models

from .recurrence_rule import RecurrenceRule
from ..pois.poi import POI
from ..regions.region import Region
from ...constants import frequency, status


class Event(models.Model):
    """
    Data model representing an event.

    :param id: The database id of the event
    :param start_date: The date when the event starts
    :param start_time: The time when the event starts
    :param end_date: The date when the event ends
    :param end_time: The time when the event ends
    :param picture: The thumbnail image of the event
    :param archived: Whether or not the event is archived

    Relationship fields:

    :param region: The region to which the event belongs (related name: ``events``)
    :param location: The point of interest where the event takes place (related name: ``events``)
    :param recurrence_rule: If the event is recurring, the recurrence rule contains all necessary information on the
                            frequency, interval etc. which is needed to calculate the single instances of a recurring
                            event (related name: ``events``)

    Reverse relationships:

    :param translations: The translations of this event
    :param feedback: The feedback to this event
    """

    region = models.ForeignKey(Region, related_name="events", on_delete=models.CASCADE)
    location = models.ForeignKey(
        POI, related_name="events", on_delete=models.PROTECT, null=True, blank=True
    )
    start_date = models.DateField()
    start_time = models.TimeField(blank=True)
    end_date = models.DateField()
    end_time = models.TimeField(blank=True)
    recurrence_rule = models.OneToOneField(
        RecurrenceRule, null=True, on_delete=models.SET_NULL
    )
    picture = models.ImageField(null=True, blank=True, upload_to="events/%Y/%m/%d")
    archived = models.BooleanField(default=False)

    @property
    def languages(self):
        """
        This property returns a list of all :class:`~cms.models.languages.language.Language` objects, to which an event
        translation exists.

        :return: list of all :class:`~cms.models.languages.language.Language` an event is translated into
        :rtype: list [ ~cms.models.languages.language.Language ]
        """
        event_translations = self.translations.prefetch_related("language").all()
        languages = []
        for event_translation in event_translations:
            languages.append(event_translation.language)
        return languages

    @property
    def is_recurring(self):
        """
        This property checks if the event has a recurrence rule and thereby determines, whether the event is recurring.

        :return: Whether the event is recurring or not
        :rtype: bool
        """
        return bool(self.recurrence_rule)

    @property
    def is_all_day(self):
        """
        This property checks whether an event takes place the whole day by checking if start time is minimal and end
        time is maximal.

        :return: Whether event takes place all day
        :rtype: bool
        """
        return self.start_time == time.min and self.end_time == time.max.replace(
            second=0, microsecond=0
        )

    @property
    def has_location(self):
        """
        This property checks whether the event has a physical location (:class:`~cms.models.pois.poi.POI`).

        :return: Whether event has a physical location
        :rtype: bool
        """
        return bool(self.location)

    def get_translation(self, language_code):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~cms.models.languages.language.Language` code.

        :param language_code: The code of the desired :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The event translation in the requested :class:`~cms.models.languages.language.Language` or :obj:`None`
                 if no translation exists
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(language__code=language_code).first()

    @classmethod
    def get_list(cls, region_slug, archived=False):
        """
        Get events of one specific :class:`~cms.models.regions.region.Region` (either all archived or all not archived
        ones)

        :param region_slug: slug of the :class:`~cms.models.regions.region.Region` the event belongs to
        :type region_slug: str

        :param archived: whether or not archived events should be returned, defaults to ``False``
        :type archived: bool, optional

        :return: A :class:`~django.db.models.query.QuerySet` of either archived or not archived events in the requested
                 :class:`~cms.models.regions.region.Region`
        :rtype: ~django.db.models.query.QuerySet
        """
        events = (
            cls.objects.all()
            .prefetch_related("translations")
            .filter(region__slug=region_slug, archived=archived)
        )
        return events

    def get_occurrences(self, start, end):
        """
        Get occurrences of the event that overlap with ``[start, end]``.
        Expects ``start < end``.

        :param start: the begin of the requested interval.
        :type start: ~datetime.datetime

        :param end: the end of the requested interval.
        :type end: ~datetime.datetime

        :return: Returns start datetimes of occurrences of the event that are in the given timeframe
        :rtype: list [ ~datetime.datetime ]
        """
        event_start = datetime.combine(
            self.start_date, self.start_time if self.start_time else time.min
        )
        event_end = datetime.combine(
            self.end_date, self.end_time if self.end_time else time.max
        )
        event_span = event_end - event_start
        recurrence = self.recurrence_rule
        if recurrence is not None:
            until = min(
                end,
                datetime.combine(
                    recurrence.recurrence_end_date
                    if recurrence.recurrence_end_date
                    else date.max,
                    time.max,
                ),
            )
            if recurrence.frequency in (frequency.DAILY, frequency.YEARLY):
                occurrences = rrule(
                    recurrence.frequency,
                    dtstart=event_start,
                    interval=recurrence.interval,
                    until=until,
                )
            elif recurrence.frequency == frequency.WEEKLY:
                occurrences = rrule(
                    recurrence.frequency,
                    dtstart=event_start,
                    interval=recurrence.interval,
                    byweekday=recurrence.weekdays_for_weekly,
                    until=until,
                )
            else:
                occurrences = rrule(
                    recurrence.frequency,
                    dtstart=event_start,
                    interval=recurrence.interval,
                    byweekday=weekday(
                        recurrence.weekday_for_monthly, recurrence.week_for_monthly
                    ),
                    until=until,
                )
            return [
                x
                for x in occurrences
                if start <= x <= end or start <= x + event_span <= end
            ]
        return (
            [event_start]
            if start <= event_start <= end or start <= event_end <= end
            else []
        )

    def get_public_translation(self, language_code):
        """
        This function retrieves the newest public translation of an event.

        :param language_code: The code of the requested :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The public translation of an event
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(
            language__code=language_code,
            status=status.PUBLIC,
        ).first()

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param ordering: The fields which are used to sort the returned objects of a QuerySet
        :type ordering: list [ str ]

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple

        :param permissions: The custom permissions for this model
        :type permissions: tuple
        """

        ordering = ["start_date", "start_time"]
        default_permissions = ()
        permissions = (
            ("view_events", "Can view events"),
            ("edit_events", "Can edit events"),
            ("publish_events", "Can publish events"),
        )
