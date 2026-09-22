"""
This module contains the states a translation can have
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Up to date
UP_TO_DATE: Final = "UP_TO_DATE"
#: In translation
IN_TRANSLATION: Final = "IN_TRANSLATION"
#: Outdated
OUTDATED: Final = "OUTDATED"
#: Fallback
FALLBACK: Final = "FALLBACK"
#: Missing
MISSING: Final = "MISSING"
#: Machine translated
MACHINE_TRANSLATED: Final = "MACHINE_TRANSLATED"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (UP_TO_DATE, _("Translation up-to-date")),
    (IN_TRANSLATION, _("Currently in translation")),
    (OUTDATED, _("Translation outdated")),
    # Do not show fallback translations in translation coverage
    # (FALLBACK, _("Default language is duplicated")),
    (MISSING, _("Translation missing")),
    (MACHINE_TRANSLATED, _("Machine translated")),
]

#: Maps from the translation state to the color used to render this state in the translation coverage view
COLORS: Final[dict[str, str]] = {
    UP_TO_DATE: "#4ade80",
    IN_TRANSLATION: "#60a5fa",
    OUTDATED: "#facc15",
    MACHINE_TRANSLATED: "#9933ff",
    # Do not show fallback translations in translation coverage
    # FALLBACK: "#60a5fa",
    MISSING: "#f87171",
}
