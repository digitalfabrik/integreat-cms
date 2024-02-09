"""
This module contains string representations of permission levels for machine
translations, used by :class:`~integreat_cms.cms.models.regions.region.Region`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Machine Translations are disabled
NO_ONE: Final = 0
#: Everyone can use Machine Translation
EVERYONE: Final = 1
#: Only Managers can use Machine Translations
MANAGERS: Final = 2

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[int, Promise]]] = [
    (NO_ONE, _("No")),
    (EVERYONE, _("Yes")),
    (MANAGERS, _("Yes, only managers")),
]
