"""
This module contains all string representations of recurrence filter options, used by :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~integreat_cms.cms.views.events.event_list_view.EventListView`:

The module also contains a constant :const:`~integreat_cms.cms.constants.recurrence.DATATYPE` which contains the type of the constant values linked to the strings and is used for correctly
instantiating :class:`django.forms.TypedMultipleChoiceField` instances in :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

#: This docstring is overridden by "alias of builtins.int"
DATATYPE: Final = int

#: Events that are recurring, i.e. take place more than once
RECURRING: Final = 1
#: Events that are not recurring and only take place on one day
ONE_TIME: Final = 2
#: Events that are not recurring but take place over a long period of time
LONG_TERM: Final = 3

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[int, Promise]]] = [
    (RECURRING, _("Recurring events")),
    (ONE_TIME, _("One time events")),
    (LONG_TERM, _("Long term events")),
]
