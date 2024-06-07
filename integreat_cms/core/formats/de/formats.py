"""
This file contains locale formats to override the default ones.
See :setting:`django:FORMAT_MODULE_PATH` and :attr:`~integreat_cms.core.settings.FORMAT_MODULE_PATH` for more information.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

#: The default formatting to use for displaying datetime fields in any part of the system when using the German locale.
DATETIME_FORMAT: Final[str] = "d.m.Y, H:i"

#: The short formatting to use for displaying datetime fields when the time is irrelevant
SHORT_DATE_FORMAT: Final[str] = "d.m.Y"
