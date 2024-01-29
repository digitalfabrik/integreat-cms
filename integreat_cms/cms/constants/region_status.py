"""
This module contains the possible status of regions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Active
ACTIVE: Final = "ACTIVE"
#: Hidden
HIDDEN: Final = "HIDDEN"
#: Archived
ARCHIVED: Final = "ARCHIVED"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (ACTIVE, _("Active")),
    (HIDDEN, _("Hidden")),
    (ARCHIVED, _("Archived")),
]
