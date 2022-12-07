"""
This module contains all string representations of months, used by :class:`~integreat_cms.cms.models.events.event.Event`.
"""
from django.utils.translation import gettext_lazy as _


#: January
JANUARY = 0
#: February
FEBRUARY = 1
#: March
MARCH = 2
#: April
APRIL = 3
#: May
MAY = 4
#: June
JUNE = 5
#: July
JULY = 6
#: August
AUGUST = 7
#: September
SEPTEMBER = 8
#: October
OCTOBER = 9
#: November
NOVEMBER = 10
#: December
DECEMBER = 11

#: Choices to use these constants in a database field
CHOICES = (
    (JANUARY, _("January")),
    (FEBRUARY, _("February")),
    (MARCH, _("March")),
    (APRIL, _("April")),
    (MAY, _("May")),
    (JUNE, _("June")),
    (JULY, _("July")),
    (AUGUST, _("August")),
    (SEPTEMBER, _("September")),
    (OCTOBER, _("October")),
    (NOVEMBER, _("November")),
    (DECEMBER, _("December")),
)
