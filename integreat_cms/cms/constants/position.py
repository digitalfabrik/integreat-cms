"""
This module contains all possible positions inside a MPTT tree model.
It is used to determine the relative position of nodes in relation to another node.
"""
from django.utils.translation import gettext_lazy as _


#: First child of node
FIRST_CHILD = "first-child"
#: Last child of node
LAST_CHILD = "last-child"
#: Left neighbor of node
LEFT = "left"
#: Right neighbor of node
RIGHT = "right"
#: First sibling of node
FIRST_SIBLING = "first-sibling"
#: Last sibling of node
LAST_SIBLING = "last-sibling"

#: Choices to use these constants in a database field
CHOICES = (
    (FIRST_CHILD, _("First subpage of")),
    (LAST_CHILD, _("Last subpage of")),
    (LEFT, _("Left neighbor of")),
    (RIGHT, _("Right neighbor of")),
)
