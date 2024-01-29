"""
This module contains all possible positions inside a MPTT tree model.
It is used to determine the relative position of nodes in relation to another node.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: First child of node
FIRST_CHILD: Final = "first-child"
#: Last child of node
LAST_CHILD: Final = "last-child"
#: Left neighbor of node
LEFT: Final = "left"
#: Right neighbor of node
RIGHT: Final = "right"
#: First sibling of node
FIRST_SIBLING: Final = "first-sibling"
#: Last sibling of node
LAST_SIBLING: Final = "last-sibling"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (FIRST_CHILD, _("First subpage of")),
    (LAST_CHILD, _("Last subpage of")),
    (LEFT, _("Left neighbor of")),
    (RIGHT, _("Right neighbor of")),
]
