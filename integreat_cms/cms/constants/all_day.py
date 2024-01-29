"""
This module contains all string representations of all day filter options, used by :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~integreat_cms.cms.views.events.event_list_view.EventListView`.

The module also contains a constant :attr:`~integreat_cms.cms.constants.all_day.DATATYPE`, which contains the type of the constant
values linked to the strings and is used for correctly instantiating :class:`django.forms.TypedMultipleChoiceField`
instances in :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: This docstring is overridden by "alias of builtins.int"
DATATYPE: Final = int

#: Only events which are all day long
ALL_DAY: Final = 1
#: Exclude events which are all day long
NOT_ALL_DAY: Final = 2

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[int, Promise]]] = [
    (ALL_DAY, _("All day long events")),
    (NOT_ALL_DAY, _("Not all day long events")),
]
