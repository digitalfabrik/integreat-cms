"""
This module contains all constants representing the frequency of an :class:`~integreat_cms.cms.models.events.event.Event`'s
:class:`~integreat_cms.cms.models.events.recurrence_rule.RecurrenceRule`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Daily
DAILY: Final = "DAILY"
#: Weekly
WEEKLY: Final = "WEEKLY"
#: Monthly
MONTHLY: Final = "MONTHLY"
#: Yearly
YEARLY: Final = "YEARLY"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (DAILY, _("Daily")),
    (WEEKLY, _("Weekly")),
    (MONTHLY, _("Monthly")),
    (YEARLY, _("Yearly")),
]
