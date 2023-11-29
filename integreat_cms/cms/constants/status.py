"""
This module contains the possible status of translations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Draft
DRAFT: Final = "DRAFT"
#: Pending Approval
REVIEW: Final = "REVIEW"
#: Public
PUBLIC: Final = "PUBLIC"
#: Auto Save
AUTO_SAVE: Final = "AUTO_SAVE"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (DRAFT, _("Draft")),
    (REVIEW, _("Pending Approval")),
    (PUBLIC, _("Published")),
    (AUTO_SAVE, _("Auto Save")),
]
