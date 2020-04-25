"""
This module contains all possible positions inside a MPTT tree model.
It is used to determine the relative position of pages in relation to another page.
Possible values are:

* ``FIRST_CHILD``: First child of page

* ``LAST_CHILD``: Last child of page

* ``LEFT``: Left neighbor of page

* ``RIGHT``: Right neighbor of page
"""

from django.utils.translation import ugettext_lazy as _


FIRST_CHILD = 'first-child'
LAST_CHILD = 'last-child'
LEFT = 'left'
RIGHT = 'right'

CHOICES = (
    (FIRST_CHILD, _('First child of')),
    (LAST_CHILD, _('Last child of')),
    (LEFT, _('Left neighbor of')),
    (RIGHT, _('Right neighbor of'))
    )
