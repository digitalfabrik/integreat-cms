"""
This module contains all constants representing the text directions of a :class:`~integreat_cms.cms.models.languages.language.Language`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Text is left to right, e.g. in English
LEFT_TO_RIGHT: Final = "LEFT_TO_RIGHT"
#: Text is right to left, e.g. in Arabic
RIGHT_TO_LEFT: Final = "RIGHT_TO_LEFT"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (LEFT_TO_RIGHT, _("Left to right")),
    (RIGHT_TO_LEFT, _("Right to left")),
]
