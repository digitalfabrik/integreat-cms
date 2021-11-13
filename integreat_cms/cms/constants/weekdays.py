"""
This module contains all string representations of weekdays, used by :class:`~integreat_cms.cms.models.events.event.Event`.
"""
from django.utils.translation import ugettext_lazy as _


#: Monday
MONDAY = 0
#: Tuesday
TUESDAY = 1
#: Wednesday
WEDNESDAY = 2
#: Thursday
THURSDAY = 3
#: Friday
FRIDAY = 4
#: Saturday
SATURDAY = 5
#: Sunday
SUNDAY = 6

#: Choices to use these constants in a database field
CHOICES = (
    (MONDAY, _("Monday")),
    (TUESDAY, _("Tuesday")),
    (WEDNESDAY, _("Wednesday")),
    (THURSDAY, _("Thursday")),
    (FRIDAY, _("Friday")),
    (SATURDAY, _("Saturday")),
    (SUNDAY, _("Sunday")),
)
