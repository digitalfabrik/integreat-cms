"""
This module contains all constants representing the frequency of an :class:`~cms.models.events.event.Event`'s
:class:`~cms.models.events.recurrence_rule.RecurrenceRule`:

* ``DAILY``: Daily

* ``WEEKLY``: Weekly

* ``MONTHLY``: Monthly

* ``YEARLY``: Yearly
"""

from django.utils.translation import ugettext_lazy as _


DAILY = "DAILY"
WEEKLY = "WEEKLY"
MONTHLY = "MONTHLY"
YEARLY = "YEARLY"

CHOICES = (
    (DAILY, _("Daily")),
    (WEEKLY, _("Weekly")),
    (MONTHLY, _("Monthly")),
    (YEARLY, _("Yearly")),
)
