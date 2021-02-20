"""
This module contains all string representations of all day filter options, used by :class:`~cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~cms.views.events.event_list_view.EventListView`.

The module also contains a constant :attr:`~cms.constants.all_day.DATATYPE`, which contains the type of the constant
values linked to the strings and is used for correctly instantiating :class:`django.forms.TypedMultipleChoiceField`
instances in :class:`~cms.forms.events.event_filter_form.EventFilterForm`.
"""
from django.utils.translation import ugettext_lazy as _


#: Only events which are all day long
READ = True
#: Exclude events which are all day long
UNREAD = False

#: Choices to use these constants in a database field
CHOICES = [
    (READ, _("Read")),
    (UNREAD, _("Unread")),
]

INITIAL = [key for (key, val) in CHOICES]
