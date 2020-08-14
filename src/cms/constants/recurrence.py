"""
This module contains all string representations of recurrence filter options, used by :class:`~cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~cms.views.events.event_list_view.EventListView`:

* ``RECURRING``: Events that are recurring, i.e. take place more than once

* ``NOT_RECURRING``: Events that are not recurring, i.e. take place only once

The module also contains a constant ``DATATYPE`` which contains the type of the constant values linked to the strings and is used for correctly
instantiating :class:`django.forms.TypedMultipleChoiceField` instances in :class:`~cms.forms.events.event_filter_form.EventFilterForm`.
"""
from django.utils.translation import ugettext_lazy as _

DATATYPE = int

RECURRING = 1
NOT_RECURRING = 2

CHOICES = (
    (RECURRING, _("Recurring events")),
    (NOT_RECURRING, _("Non-recurring events")),
)
