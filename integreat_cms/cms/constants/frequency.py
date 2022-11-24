"""
This module contains all constants representing the frequency of an :class:`~integreat_cms.cms.models.events.event.Event`'s
:class:`~integreat_cms.cms.models.events.recurrence_rule.RecurrenceRule`.
"""
from django.utils.translation import gettext_lazy as _


#: Daily
DAILY = "DAILY"
#: Weekly
WEEKLY = "WEEKLY"
#: Monthly
MONTHLY = "MONTHLY"
#: Yearly
YEARLY = "YEARLY"

#: Choices to use these constants in a database field
CHOICES = (
    (DAILY, _("Daily")),
    (WEEKLY, _("Weekly")),
    (MONTHLY, _("Monthly")),
    (YEARLY, _("Yearly")),
)
