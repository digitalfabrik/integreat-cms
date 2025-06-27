"""
This module contains the available choices for machine translation budget
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final


MINIMAL: Final = 50000
TINY: Final = 100000
SMALL: Final = 150000
MEDIUM: Final = 250000
LARGE: Final = 1000000
HUGE: Final = 5000000

CHOICES: Final[list[tuple[int, str]]] = [
    (MINIMAL, "50.000"),
    (TINY, "100.000"),
    (SMALL, "150.000"),
    (MEDIUM, "250.000"),
    (LARGE, "1.000.000"),
    (HUGE, "5.000.000"),
]
