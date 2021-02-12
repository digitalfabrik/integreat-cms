"""
This module contains all possible positions inside a MPTT tree model.
It is used to determine the relative position of pages in relation to another page.
"""
from django.utils.translation import ugettext_lazy as _


#: First child of page
FIRST_CHILD = "first-child"
#: Last child of page
LAST_CHILD = "last-child"
#: Left neighbor of page
LEFT = "left"
#: Right neighbor of page
RIGHT = "right"

#: Choices to use these constants in a database field
CHOICES = (
    (FIRST_CHILD, _("First subpage of")),
    (LAST_CHILD, _("Last subpage of")),
    (LEFT, _("Left neighbor of")),
    (RIGHT, _("Right neighbor of")),
)
