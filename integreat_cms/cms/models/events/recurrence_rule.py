from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

from dateutil import rrule
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import make_aware
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from ...constants import frequency, weekdays, weeks
from ..abstract_base_model import AbstractBaseModel

if TYPE_CHECKING:
    from typing import Iterator


class RecurrenceRule(AbstractBaseModel):
    """
    Data model representing the recurrence frequency and interval of an event
    """

    #: Manage choices in :mod:`~integreat_cms.cms.constants.frequency`
    frequency = models.CharField(
        max_length=7,
        choices=frequency.CHOICES,
        default=frequency.WEEKLY,
        verbose_name=_("frequency"),
        help_text=_("How often the event recurs"),
    )
    interval = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Repeat every ... time(s)"),
        help_text=_("The interval in which the event recurs."),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.weekdays`
    weekdays_for_weekly = ArrayField(
        models.IntegerField(choices=weekdays.CHOICES),
        blank=True,
        verbose_name=_("weekdays"),
        help_text=_(
            "If the frequency is weekly, this field determines on which days the event takes place"
        ),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.weekdays`
    weekday_for_monthly = models.IntegerField(
        choices=weekdays.CHOICES,
        null=True,
        blank=True,
        verbose_name=_("weekday"),
        help_text=_(
            "If the frequency is monthly, this field determines on which days the event takes place"
        ),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.weeks`
    week_for_monthly = models.IntegerField(
        choices=weeks.CHOICES,
        null=True,
        blank=True,
        verbose_name=_("week"),
        help_text=_(
            "If the frequency is monthly, this field determines on which week of the month the event takes place"
        ),
    )
    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("recurrence end date"),
        help_text=_(
            "If the recurrence is not for an indefinite period, this field contains the end date"
        ),
    )

    def iter_after(self, start_date: date) -> Iterator[date]:
        """
        Iterate all recurrences after a given start date.
        This method assumes that ``weekdays_for_weekly`` contains at least one member
        and that ``weekday_for_monthly`` and ``week_for_monthly`` are not null.

        :param start_date: The date on which the iteration should start
        :return: An iterator over all dates defined by this recurrence rule
        """
        next_recurrence = start_date

        def get_nth_weekday(month_date: date, weekday: int, n: int) -> date:
            """
            Get the nth occurrence of a given weekday in a specific month

            :param month_date: the current date of month
            :param weekday: the requested weekday
            :param n: the requested number
            :return: The nth weekday
            """
            month_date = month_date.replace(day=1)
            month_date += timedelta((weekday - month_date.weekday()) % 7)
            n_th_occurrence = month_date + timedelta(weeks=n - 1)
            # If the occurrence is not in the desired month (because the last week is 4 and not 5), retry with 4
            if n_th_occurrence.month != month_date.month:
                n_th_occurrence = month_date + timedelta(weeks=n - 2)
            return n_th_occurrence

        def next_month(month_date: date) -> date:
            """
            Advance the given date by one month

            :param month_date: the given date
            :return: The same date one month later
            """
            month_date = month_date.replace(day=1)
            if month_date.month < 12:
                return month_date.replace(month=month_date.month + 1)
            return month_date.replace(month=1, year=month_date.year + 1)

        def advance() -> Iterator[date]:
            """
            Get the next occurrence by this rule

            :return: date objects
            """

            nonlocal next_recurrence
            if self.frequency == frequency.DAILY:
                yield next_recurrence
                next_recurrence += timedelta(days=1)
            elif self.frequency == frequency.WEEKLY:
                # Yield each day of the week that is valid, since
                # ``interval`` should apply here only on weekly basis
                for weekday in sorted(self.weekdays_for_weekly):
                    if weekday < next_recurrence.weekday():
                        continue
                    next_recurrence += timedelta(
                        days=weekday - next_recurrence.weekday()
                    )
                    yield next_recurrence
                # advance to the next monday
                next_recurrence += timedelta(days=7 - next_recurrence.weekday())
            elif self.frequency == frequency.MONTHLY:
                next_recurrence = get_nth_weekday(
                    next_recurrence, self.weekday_for_monthly, self.week_for_monthly
                )
                if next_recurrence < start_date:
                    next_recurrence = get_nth_weekday(
                        next_month(next_recurrence),
                        self.weekday_for_monthly,
                        self.week_for_monthly,
                    )
                yield next_recurrence
                next_recurrence = next_month(next_recurrence)
            elif self.frequency == frequency.YEARLY:
                yield next_recurrence

                # It is not possible to go simply to the next year if the current date is february 29
                year_dif = 1
                while True:
                    try:
                        next_recurrence = next_recurrence.replace(
                            year=next_recurrence.year + year_dif
                        )
                        break
                    except ValueError:
                        year_dif += 1

        i = 0
        end_date = self.recurrence_end_date or date.max
        while True:
            for _recurrence in advance():
                if next_recurrence > end_date:
                    return
                if not i % self.interval:
                    yield next_recurrence
            i += 1

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``RecurrenceRule object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the recurrence rule
        """
        return gettext('Recurrence rule of "{}" ({})').format(
            self.event.best_translation.title, self.get_frequency_display()
        )

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<RecurrenceRule: RecurrenceRule object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the recurrence rule
        """
        return f"<RecurrenceRule (id: {self.id}, event: {self.event.best_translation.slug})>"

    def to_ical_rrule(self) -> rrule.rrule:
        """
        Calculates the ical standardized rrule for a recurring rule. See details of the rrule here:
        https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html

        :return: The ical rrule for the recurrence rule
        """
        kwargs = {}
        if self.frequency == frequency.WEEKLY:
            kwargs["byweekday"] = self.weekdays_for_weekly
        elif self.frequency == frequency.MONTHLY:
            kwargs["byweekday"] = rrule.weekday(
                self.weekday_for_monthly, self.week_for_monthly
            )
        if self.recurrence_end_date:
            kwargs["until"] = make_aware(
                datetime.combine(self.recurrence_end_date, time.max),
                self.event.start.tzinfo,
            )

        ical_rrule = rrule.rrule(
            getattr(rrule, self.frequency),
            dtstart=self.event.start,
            interval=self.interval,
            **kwargs,
        )
        return ical_rrule

    def to_ical_rrule_string(self) -> str:
        """
        Gets the iCal rrule as a string

        :return: The ical rrule for the recurrence rule as a string
        """
        return str(self.to_ical_rrule())

    class Meta:
        #: The verbose name of the model
        verbose_name = _("recurrence rule")
        #: The plural verbose name of the model
        verbose_name_plural = _("recurrence rules")
        #: The default permissions for this model
        default_permissions = ()
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["pk"]
