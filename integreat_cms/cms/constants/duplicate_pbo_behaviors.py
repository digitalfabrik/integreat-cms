"""
This module contains all possible behaviors available when cloning regions and having
to decide how to handle page based offers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


ACTIVATE: Final = "activate_missing"
DISCARD: Final = "discard_missing"

CHOICES: Final[list[tuple[str, Promise]]] = [
    (ACTIVATE, _("Activate all required offers, regardless of choices above")),
    (DISCARD, _("Discard offer embeddings from offers not activated manually")),
]
