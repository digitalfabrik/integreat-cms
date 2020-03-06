"""Class defining event-related database models

Raises:
    ValidationError: Raised when an value does not match the requirements
"""
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from ...constants import frequency, weekdays, weeks


class RecurrenceRule(models.Model):
    """
    Object to define the recurrence frequency
    Args:
        models ([type]): [description]
    Raises:
        ValidationError: Error raised when weekdays_for_weekly does not fit into the range
        from 0 to 6 or when the value of weekdays_for_monthly isn't between -5 and 5.
    """

    frequency = models.CharField(max_length=7, choices=frequency.CHOICES, blank=True)
    interval = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    weekdays_for_weekly = ArrayField(models.IntegerField(choices=weekdays.CHOICES), blank=True)
    weekday_for_monthly = models.IntegerField(choices=weekdays.CHOICES, null=True, blank=True)
    week_for_monthly = models.IntegerField(choices=weeks.CHOICES, null=True, blank=True)
    recurrence_end_date = models.DateField(null=True, blank=True)
