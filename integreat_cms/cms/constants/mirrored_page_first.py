"""
This module contains labels for the choices regarding the position of embedding live content
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

MIRRORED_PAGE_BEFORE: Final = True
MIRRORED_PAGE_AFTER: Final = False

CHOICES: Final[list[tuple[bool, Promise]]] = [
    (MIRRORED_PAGE_BEFORE, _("Embed mirrored page before this page")),
    (MIRRORED_PAGE_AFTER, _("Embed mirrored page after this page")),
]
