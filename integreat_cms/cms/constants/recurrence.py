"""
This module contains all string representations of recurrence filter options, used by :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~integreat_cms.cms.views.events.event_list_view.EventListView`:

The module also contains a constant :const:`~integreat_cms.cms.constants.recurrence.DATATYPE` which contains the type of the constant values linked to the strings and is used for correctly
instantiating :class:`django.forms.TypedMultipleChoiceField` instances in :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm`.
"""
from django.utils.translation import gettext_lazy as _


#: This docstring is overridden by "alias of builtins.int"
DATATYPE = int

#: Events that are recurring, i.e. take place more than once
RECURRING = 1
#: Events that are not recurring, i.e. take place only once
NOT_RECURRING = 2

#: Choices to use these constants in a database field
CHOICES = (
    (RECURRING, _("Recurring events")),
    (NOT_RECURRING, _("Non-recurring events")),
)
