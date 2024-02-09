"""
This module contains colors which aim to be good distinguishable by humans.
They are used to display graphs with overlapping lines (e.g. statistics).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final


#: The default color (blue-500 from tailwind css).
DEFAULT: Final = "#3b82f6"

#: A list of 20 distinguishable colors (taken from https://sashamaps.net/docs/resources/20-colors/)
CHOICES: Final[list[str]] = [
    "#e6194b",
    "#000075",
    "#ffe119",
    "#f58231",
    "#3cb44b",
    "#46f0f0",
    "#f032e6",
    "#800000",
    "#fffac8",
    "#aaffc3",
    "#bcf60c",
    "#4363d8",
    "#008080",
    "#9a6324",
    "#911eb4",
    "#808000",
    "#e6beff",
    "#808080",
    "#fabebe",
    "#ffd8b1",
]
