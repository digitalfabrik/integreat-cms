"""
This module contains all string representations of weekdays, used by :class:`~integreat_cms.cms.models.events.event.Event`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Monday
MONDAY: Final = 0
#: Tuesday
TUESDAY: Final = 1
#: Wednesday
WEDNESDAY: Final = 2
#: Thursday
THURSDAY: Final = 3
#: Friday
FRIDAY: Final = 4
#: Saturday
SATURDAY: Final = 5
#: Sunday
SUNDAY: Final = 6

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[int, Promise]]] = [
    (MONDAY, _("Monday")),
    (TUESDAY, _("Tuesday")),
    (WEDNESDAY, _("Wednesday")),
    (THURSDAY, _("Thursday")),
    (FRIDAY, _("Friday")),
    (SATURDAY, _("Saturday")),
    (SUNDAY, _("Sunday")),
]

#: Working days: Monday to Friday
WORKING_DAYS: Final[list[int]] = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY]

#: Weekend: Saturday and Sunday
WEEKEND: Final[list[int]] = [SATURDAY, SUNDAY]
