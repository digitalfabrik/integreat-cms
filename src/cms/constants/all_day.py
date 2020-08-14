"""
This module contains all string representations of all day filter options, used by :class:`~cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~cms.views.events.event_list_view.EventListView`:

* ``ALL_DAY``: Only events which are all day long

* ``NOT_ALL_DAY``: Exclude events which are all day long

The module also contains a constant ``DATATYPE`` which contains the type of the constant values linked to the strings and is used for correctly
instantiating :class:`django.forms.TypedMultipleChoiceField` instances in :class:`~cms.forms.events.event_filter_form.EventFilterForm`.
"""
from django.utils.translation import ugettext_lazy as _

DATATYPE = int

ALL_DAY = 1
NOT_ALL_DAY = 2

CHOICES = (
    (ALL_DAY, _("All day long events")),
    (NOT_ALL_DAY, _("Not all day long events")),
)
