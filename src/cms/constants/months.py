"""
This module contains all string representations of months, used by events:

* ``JANUARY``: January

* ``FEBRUARY``: February

* ``MARCH``: March

* ``APRIL``: April

* ``MAY``: May

* ``JUNE``: June

* ``JULY``: July

* ``AUGUST``: August

* ``SEPTEMBER``: September

* ``OCTOBER``: October

* ``NOVEMBER``: November

* ``DECEMBER``: December

"""
from django.utils.translation import ugettext_lazy as _


JANUARY = 0
FEBRUARY = 1
MARCH = 2
APRIL = 3
MAY = 4
JUNE = 5
JULY = 6
AUGUST = 7
SEPTEMBER = 8
OCTOBER = 9
NOVEMBER = 10
DECEMBER = 11

CHOICES = (
    (JANUARY, _('January')),
    (FEBRUARY, _('February')),
    (MARCH, _('March')),
    (APRIL, _('April')),
    (MAY, _('May')),
    (JUNE, _('June')),
    (JULY, _('July')),
    (AUGUST, _('August')),
    (SEPTEMBER, _('September')),
    (OCTOBER, _('October')),
    (NOVEMBER, _('November')),
    (DECEMBER, _('December'))
)
