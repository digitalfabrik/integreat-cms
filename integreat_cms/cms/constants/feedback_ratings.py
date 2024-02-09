"""
This module contains all constants representing the rating of the :class:`~integreat_cms.cms.models.feedback.feedback.Feedback` model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Positive
POSITIVE: Final = True
#: Negative
NEGATIVE: Final = False
#: Not stated
NOT_STATED: Final = None
#: Not stated as string (used in the filter form)
NOT_STATED_STR: Final = ""

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[bool | None, Promise]]] = [
    (POSITIVE, _("Positive")),
    (NEGATIVE, _("Negative")),
    (NOT_STATED, _("Not stated")),
]

#: Choices for the filter form (required because ``None`` is always converted to ``""``)
FILTER_CHOICES: Final[list[tuple[bool | str, Promise]]] = [
    (POSITIVE, _("Positive")),
    (NEGATIVE, _("Negative")),
    (NOT_STATED_STR, _("Not stated")),
]

#: Initial filter options
INITIAL: Final[list[bool | str]] = [key for (key, val) in FILTER_CHOICES]
