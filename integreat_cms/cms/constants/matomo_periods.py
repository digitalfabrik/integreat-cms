"""
This module contains all constants representing the period choices for the Matomo API
(See https://developer.matomo.org/api-reference/reporting-api).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Daily
DAY: Final = "day"
#: Weekly
WEEK: Final = "week"
#: Monthly
MONTH: Final = "month"
#: Yearly
YEAR: Final = "year"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (DAY, _("Daily")),
    (WEEK, _("Weekly")),
    (MONTH, _("Monthly")),
    (YEAR, _("Yearly")),
]
