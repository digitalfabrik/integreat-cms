"""
This module contains constants for Language model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from ..utils.translation_utils import gettext_many_lazy as __

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

MELLOW_APRICOT: Final = "#FFBB78"
FOREST_GREEN: Final = "#2CA02C"
ROSE: Final = "#FF9896"
TROPICAL_VIOLET: Final = "#C5B0D5"
RED: Final = "#FF4500"
ORANGE: Final = "#FFA500"
DARK_BLUE: Final = "#17157D"
GREEN_BLUE: Final = "#1F77B4"
YELLOW: Final = "#FFD700"
TEAL: Final = "#008080"
ARCTIC: Final = "#9EDAE5"
AZURE: Final = "#5894E3"
PACIFIC_BLUE: Final = "#17BECF"
ORANGE_RED: Final = "#FF6347"
LIGHT_GREEN: Final = "#98DF8A"
VIOLET: Final = "#9467BD"
LIME: Final = "#ADFF2F"
LAVENDER: Final = "#E377C2"
BROWN: Final = "#8C564B"
PINK_ORANGE: Final = "#FFA07A"
PASTEL_PINK: Final = "#FFE4F0"
KHAKI: Final = "#F0E68C"
YELLOW_GREEN: Final = "#BCBD22"
MAUVE: Final = "#800080"
PURPLE: Final = "#BA55D3"
PRIMROSE: Final = "#DBDB8D"
FIORD: Final = "#4B5563"
QUICKSAND: Final = "#C49C94"
GREY: Final = "#7F7F7F"
AQUA: Final = "#26FCFF"
PINE_GREEN: Final = "#20B2AA"
ALMOND: Final = "#FFDAB9"
CHERRY: Final = "#D62728"

TOTAL_ACCESS: Final = "#000000"
WEB_APP_ACCESS: Final = "#FF00A8"
OFFLINE_ACCESS: Final = "#0500FF"

COLORS: Final[list[tuple[str, Promise]]] = [
    (MELLOW_APRICOT, _("Mellow apricot")),
    (FOREST_GREEN, _("Forest green")),
    (ROSE, _("Rose")),
    (TROPICAL_VIOLET, _("Tropical violet")),
    (RED, _("Red")),
    (ORANGE, _("Orange")),
    (DARK_BLUE, _("Dark blue")),
    (GREEN_BLUE, _("Green blue")),
    (YELLOW, _("Yellow")),
    (TEAL, _("Teal")),
    (ARCTIC, _("Arctic")),
    (AZURE, _("Azure")),
    (PACIFIC_BLUE, _("Pacific blue")),
    (ORANGE_RED, _("Orange red")),
    (LIGHT_GREEN, _("Light green")),
    (VIOLET, _("Violet")),
    (LIME, _("Lime")),
    (LAVENDER, _("Lavender")),
    (BROWN, _("Brown")),
    (PINK_ORANGE, _("Pink orange")),
    (PASTEL_PINK, _("Pastel pink")),
    (KHAKI, _("Khaki")),
    (YELLOW_GREEN, _("Yellow green")),
    (MAUVE, _("Mauve")),
    (PURPLE, _("Purple")),
    (PRIMROSE, _("Primrose")),
    (FIORD, _("Fiord")),
    (QUICKSAND, _("Quicksand")),
    (GREY, _("Grey")),
    (AQUA, _("Aqua")),
    (PINE_GREEN, _("Pine green")),
    (ALMOND, _("Almond")),
    (CHERRY, _("Cherry")),
]
