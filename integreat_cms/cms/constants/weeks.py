"""
This module contains all string representations of a month's week, used by :class:`~integreat_cms.cms.models.events.event.Event`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: First week of the month
FIRST: Final = 1
#: Second week of the month
SECOND: Final = 2
#: Third week of the month
THIRD: Final = 3
#: Fourth week of the month
FOURTH: Final = 4
#: Last week of the month (either 4th or 5th)
LAST: Final = 5

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[int, Promise]]] = [
    (FIRST, _("First week")),
    (SECOND, _("Second week")),
    (THIRD, _("Third week")),
    (FOURTH, _("Fourth week")),
    (LAST, _("Last week")),
]

#: A mapping from our week constants to the expected rrule values
WEEK_TO_RRULE_WEEK = {
    FIRST: 1,
    SECOND: 2,
    THIRD: 3,
    FOURTH: 4,
    LAST: -1,
}

#: A mapping from the expected rrule values to our week constants
RRULE_WEEK_TO_WEEK = {1: FIRST, 2: SECOND, 3: THIRD, 4: FOURTH, -1: LAST}
