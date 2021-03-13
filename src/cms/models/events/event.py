from datetime import datetime, time, date
from dateutil.rrule import weekday, rrule

from django.db import models
from django.utils.translation import get_language, ugettext_lazy as _

from .recurrence_rule import RecurrenceRule
from ..pois.poi import POI
from ..regions.region import Region, Language
from ...constants import frequency, status


class Event(models.Model):
    """
    Data model representing an event.
    Can be directly imported from :mod:`cms.models`.
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("region"),
    )
    location = models.ForeignKey(
        POI,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name=_("location"),
    )
    start_date = models.DateField(verbose_name=_("start date"))
    start_time = models.TimeField(blank=True, verbose_name=_("start time"))
    end_date = models.DateField(verbose_name=_("end date"))
    end_time = models.TimeField(blank=True, verbose_name=_("end time"))
    #: If the event is recurring, the recurrence rule contains all necessary information on the frequency, interval etc.
    #: which is needed to calculate the single instances of a recurring event
    recurrence_rule = models.OneToOneField(
        RecurrenceRule,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("recurrence rule"),
    )
    icon = models.ImageField(
        null=True,
        blank=True,
        upload_to="events/%Y/%m/%d",
        verbose_name=_("icon"),
    )
    archived = models.BooleanField(default=False, verbose_name=_("archived"))

    @property
    def languages(self):
        """
        This property returns a QuerySet of all :class:`~cms.models.languages.language.Language` objects, to which an event
        translation exists.

        :return: QuerySet of all :class:`~cms.models.languages.language.Language` an event is translated into
        :rtype: ~django.db.models.query.QuerySet [ ~cms.models.languages.language.Language ]
        """
        return Language.objects.filter(event_translations__event=self)

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

    def get_translation(self, language_slug):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~cms.models.languages.language.Language` slug.

        :param language_slug: The slug of the desired :class:`~cms.models.languages.language.Language`
        :type language_slug: str

        :return: The event translation in the requested :class:`~cms.models.languages.language.Language` or :obj:`None`
                 if no translation exists
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(language__slug=language_slug).first()

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

    def get_public_translation(self, language_slug):
        """
        This function retrieves the newest public translation of an event.

        :param language_slug: The slug of the requested :class:`~cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of an event
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(
            language__slug=language_slug,
            status=status.PUBLIC,
        ).first()

    @property
    def backend_translation(self):
        """
        This function returns the translation of this event in the current backend language.

        :return: The backend translation of a event
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(language__slug=get_language()).first()

    @property
    def default_translation(self):
        """
        This function returns the translation of this event in the region's default language.
        Since an event can only be created by creating a translation in the default language, this is guaranteed to return
        an event translation.

        :return: The default translation of an event
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(language=self.region.default_language).first()

    @property
    def best_translation(self):
        """
        This function returns the translation of this event in the current backend language and if it doesn't exist, it
        provides a fallback to the translation in the region's default language.

        :return: The "best" translation of an event for displaying in the backend
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.backend_translation or self.default_translation

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event")
        #: The plural verbose name of the model
        verbose_name_plural = _("events")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["start_date", "start_time"]
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (
            ("view_events", "Can view events"),
            ("edit_events", "Can edit events"),
            ("publish_events", "Can publish events"),
        )
