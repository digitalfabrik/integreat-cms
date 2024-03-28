"""
This module contains constants for Language model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final


AMHARIC: Final = "#FFBB78"
ARABIC: Final = "#2CA02C"
CZECH: Final = "#C5B0D5"
GERMAN: Final = "#FF4500"
GERMAN_EASY: Final = "#FFA500"
GREEK: Final = "#17157D"
ENGLISH: Final = "#1F77B4"
SPANISH: Final = "#FFD700"
PERSIAN: Final = "#008080"
FINNISH: Final = "#9EDAE5"
FRENCH: Final = "#5894E3"
CROATIAN: Final = "#17BECF"
HUNGARIAN: Final = "#FF6347"
ITALIAN: Final = "#98DF8A"
KURDISH: Final = "#9467BD"
SORANI: Final = "#ADFF2F"
KURMANJI: Final = "#E377C2"
DUTCH: Final = "#8C564B"
POLISH: Final = "#FFA07A"
DARI: Final = "#FFE4F0"
BRAZILIAN_PORTUGUESE: Final = "#F0E68C"
PORTUGUESE: Final = "#BCBD22"
ROMANIAN: Final = "#800080"
RUSSIAN: Final = "#BA55D3"
SOMALI: Final = "#DBDB8D"
ALBANIAN: Final = "#4B5563"
SERBIAN: Final = "#C49C94"
TIGRINYA: Final = "#7F7F7F"
TURKISH: Final = "#26FCFF"
UKRANIAN: Final = "#20B2AA"
URDU: Final = "#FFDAB9"
CHINESE_SIMPLIFIED: Final = "#D62728"

COLORS: Final = [
    (AMHARIC, _("Amharic")),
    (ARABIC, _("Arabic")),
    (CZECH, _("Czech")),
    (GERMAN, ("German")),
    (GERMAN_EASY, _("German easy")),
    (GREEK, _("Greek")),
    (ENGLISH, _("English")),
    (SPANISH, _("Spanish")),
    (PERSIAN, _("Persian")),
    (FINNISH, _("Finnish")),
    (FRENCH, _("French")),
    (CROATIAN, _("Croatian")),
    (HUNGARIAN, _("Hungarian")),
    (ITALIAN, _("Italian")),
    (KURDISH, _("Kurdish")),
    (SORANI, _("Sorani")),
    (KURMANJI, _("Kurmanji")),
    (DUTCH, _("Dutch")),
    (POLISH, _("Polish")),
    (DARI, _("Dari")),
    (BRAZILIAN_PORTUGUESE, _("Brazilian Portuguese")),
    (PORTUGUESE, _("Portuguese")),
    (ROMANIAN, _("Romanian")),
    (RUSSIAN, _("Russian")),
    (SOMALI, _("Somali")),
    (ALBANIAN, _("Albanian")),
    (SERBIAN, _("Serbian")),
    (TIGRINYA, _("Tigrinya")),
    (TURKISH, _("Turkish")),
    (UKRANIAN, _("Ukranian")),
    (URDU, _("Urdu")),
    (CHINESE_SIMPLIFIED, _("Chinese simplified")),
]
