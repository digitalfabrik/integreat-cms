from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from ...constants import frequency, weekdays, weeks


class RecurrenceRule(models.Model):
    """
    Data model representing the recurrence frequency and interval of an event

    :param id: The database id of the recurrence rule
    :param frequency: How often the event recurs (choices: :mod:`cms.constants.frequency`)
    :param interval: In which period of the frequency the event recurs ("every ``n``-th time")
    :param weekdays_for_weekly: If the frequency is weekly, this field determines on which days the event takes place
                                (choices: :mod:`cms.constants.weekdays`)
    :param weekday_for_monthly: If the frequency is monthly, this field determines on which days the event takes place
                                (choices: :mod:`cms.constants.weekdays`)
    :param week_for_monthly: If the frequency is monthly, this field determines on which week of the month the event
                             takes place (choices: :mod:`cms.constants.weeks`)
    :param recurrence_end_date: If the recurrence is not for an indefinite period, this field contains the end date

    Reverse relationships:

    :param event: The event this recurrence rule belongs to
    """

    frequency = models.CharField(max_length=7, choices=frequency.CHOICES, blank=True)
    interval = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    weekdays_for_weekly = ArrayField(
        models.IntegerField(choices=weekdays.CHOICES), blank=True
    )
    weekday_for_monthly = models.IntegerField(
        choices=weekdays.CHOICES, null=True, blank=True
    )
    week_for_monthly = models.IntegerField(choices=weeks.CHOICES, null=True, blank=True)
    recurrence_end_date = models.DateField(null=True, blank=True)
