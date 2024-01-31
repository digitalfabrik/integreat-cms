"""
This module contains all string representations of event time range filter options, used by
:class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~integreat_cms.cms.views.events.event_list_view.EventListView`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Events in the future
UPCOMING: Final = "UPCOMING"
#: Events in the past
PAST: Final = "PAST"
#: Events in a custom time range
CUSTOM: Final = "CUSTOM"

#: Choices which indicate that no filtering is required
ALL_EVENTS: list[str] = [UPCOMING, PAST]

#: Choices to use these constants in a form field
CHOICES: list[tuple[str, Promise]] = [
    (CUSTOM, _("Custom time range")),
    (UPCOMING, _("Upcoming events")),
    (PAST, _("Past events")),
]
