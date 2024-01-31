"""
This module contains all string representations of months, used by :class:`~integreat_cms.cms.models.events.event.Event`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: January
JANUARY: Final = 0
#: February
FEBRUARY: Final = 1
#: March
MARCH: Final = 2
#: April
APRIL: Final = 3
#: May
MAY: Final = 4
#: June
JUNE: Final = 5
#: July
JULY: Final = 6
#: August
AUGUST: Final = 7
#: September
SEPTEMBER: Final = 8
#: October
OCTOBER: Final = 9
#: November
NOVEMBER: Final = 10
#: December
DECEMBER: Final = 11

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[int, Promise]]] = [
    (JANUARY, _("January")),
    (FEBRUARY, _("February")),
    (MARCH, _("March")),
    (APRIL, _("April")),
    (MAY, _("May")),
    (JUNE, _("June")),
    (JULY, _("July")),
    (AUGUST, _("August")),
    (SEPTEMBER, _("September")),
    (OCTOBER, _("October")),
    (NOVEMBER, _("November")),
    (DECEMBER, _("December")),
]
