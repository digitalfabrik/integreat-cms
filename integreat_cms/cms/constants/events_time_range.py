"""
This module contains all string representations of event time range filter options, used by
:class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~integreat_cms.cms.views.events.event_list_view.EventListView`.
"""
from django.utils.translation import gettext_lazy as _


#: Events in the future
UPCOMING = "UPCOMING"
#: Events in the past
PAST = "PAST"
#: Events in a custom time range
CUSTOM = "CUSTOM"

#: Choices which indicate that no filtering is required
ALL_EVENTS = [UPCOMING, PAST]

#: Choices to use these constants in a form field
CHOICES = (
    (CUSTOM, _("Custom time range")),
    (UPCOMING, _("Upcoming events")),
    (PAST, _("Past events")),
)
