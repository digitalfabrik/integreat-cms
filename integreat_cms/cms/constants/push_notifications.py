"""
This module contains the possible modes for push notifications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final


#: Send only available translations
ONLY_AVAILABLE: Final = "ONLY_AVAILABLE"
#: Use main language if no translation is available
USE_MAIN_LANGUAGE: Final = "USE_MAIN_LANGUAGE"

#: Choices to use these constants in a database field
PN_MODES: Final = [
    (ONLY_AVAILABLE, _("Only send available translations")),
    (USE_MAIN_LANGUAGE, _("Use main language if no translation is available")),
]
