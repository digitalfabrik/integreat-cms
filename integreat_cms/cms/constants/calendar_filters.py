"""
This module contains all string representations of calendar filter options, used by :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~integreat_cms.cms.views.events.event_list_view.EventListView`:

The module also contains a constant :const:`~integreat_cms.cms.constants.calendar.DATATYPE` which contains the type of the constant values linked to the strings and is used for correctly
instantiating :class:`django.forms.TypedMultipleChoiceField` instances in :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

DATATYPE: Final = int

EVENT_NOT_FROM_EXTERNAL_CALENDAR: Final = 1
#: Events that are not recurring, i.e. take place only once
EVENT_FROM_EXTERNAL_CALENDAR: Final = 2

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[int, Promise]]] = [
    (EVENT_NOT_FROM_EXTERNAL_CALENDAR, _("Event not from an external calendar")),
    (EVENT_FROM_EXTERNAL_CALENDAR, _("Event from an external calendar")),
]
