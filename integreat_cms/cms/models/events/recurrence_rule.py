from __future__ import annotations

from datetime import date, datetime, time
from functools import cached_property
from typing import TYPE_CHECKING

from dateutil import rrule
from django.db import models
from django.utils.timezone import make_naive
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from ..abstract_base_model import AbstractBaseModel

if TYPE_CHECKING:
    from typing import Iterator


class RecurrenceRule(AbstractBaseModel):
    """
    Data model representing the recurrence frequency and interval of an event
    """

    #: An Ical (RFC 5545) compatible recurrence rule string
    raw_rule = models.CharField(verbose_name=_("Raw rule"), max_length=255)
    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("recurrence end date"),
        help_text=_(
            "If the recurrence is not for an indefinite period, this field contains the end date"
        ),
    )

    def iter_after(self, start: datetime) -> Iterator[datetime]:
        """
        Iterate all recurrences after a given start date.
        This method assumes that ``weekdays_for_weekly`` contains at least one member
        and that ``weekday_for_monthly`` and ``week_for_monthly`` are not null.

        :param start: The datetime on which the iteration should start
        :return: An iterator over all dates defined by this recurrence rule
        """
        # The rule stores all dates in utc, so it can only handle naive utc datetimes.
        naive_start = make_naive(start, timezone.utc)
        return self.to_ical_rrule().xafter(naive_start, inc=True)

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``RecurrenceRule object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the recurrence rule
        """
        return gettext('Recurrence rule of "{}" ({})').format(
            self.event.best_translation.title, self.rule
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
        return rrule.rrulestr(self.rule).replace(
            dtstart=make_naive(self.event.start, timezone=timezone.utc),
            until=make_naive(self.recurrence_end_date, timezone=timezone.utc),
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("recurrence rule")
        #: The plural verbose name of the model
        verbose_name_plural = _("recurrence rules")
        #: The default permissions for this model
        default_permissions = ()
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["pk"]
