"""
This module contains constants for POICategory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final


DARK_BLUE: Final = "#3700D2"
SKY_BLUE: Final = "#2E98FB"
CYAN: Final = "#1DC6C6"
FOREST_GREEN: Final = "#3F8F01"
LAWN_GREEN: Final = "#07DC03"
YELLOW: Final = "#F2DA04"
GOLD: Final = "#C38E03"
ORANGE: Final = "#FF7C32"
RED: Final = "#FF3333"
PINK: Final = "#EE36DC"
LAVENDER: Final = "#A258FF"
GREY: Final = "#585858"

COLORS: Final = [
    (DARK_BLUE, _("Dark blue")),
    (SKY_BLUE, _("Sky blue")),
    (CYAN, _("Cyan")),
    (FOREST_GREEN, _("Forest green")),
    (LAWN_GREEN, _("Lawn green")),
    (YELLOW, _("Yellow")),
    (GOLD, _("Gold")),
    (ORANGE, _("Orange")),
    (RED, _("Red")),
    (PINK, _("Pink")),
    (LAVENDER, _("Lavender")),
    (GREY, _("Grey")),
]

ADVICE: Final = "advice"
CULTURE: Final = "culture"
DAILY_ROUTINE: Final = "daily_routine"
EDUCATION: Final = "education"
FINANCE: Final = "finance"
GASTRONOMY: Final = "gastronomy"
HEALTH: Final = "health"
HOUSE: Final = "house"
LEISURE: Final = "leisure"
MEDIA: Final = "media"
MEDICAL_AID: Final = "medical_aid"
MEETING_POINT: Final = "meeting_point"
MENTAL_HEALTH: Final = "mental_health"
MOBILITY: Final = "mobility"
OFFICE: Final = "office"
OTHER: Final = "other"
OTHER_HELP: Final = "other_help"
SERVICE: Final = "service"
SHELTER: Final = "shelter"
SHOPPING: Final = "shopping"
STRUCTURE: Final = "structure"

ICONS: Final = [
    (ADVICE, _("Advice")),
    (CULTURE, _("Culture")),
    (DAILY_ROUTINE, _("Daily routine")),
    (EDUCATION, _("Education")),
    (FINANCE, _("Finance")),
    (GASTRONOMY, _("Gastronomy")),
    (HEALTH, _("Health")),
    (HOUSE, _("House")),
    (LEISURE, _("Leisure")),
    (MEDIA, _("Media")),
    (MEDICAL_AID, _("Medical aid")),
    (MEETING_POINT, _("Meeting point")),
    (MENTAL_HEALTH, _("Mental Health")),
    (MOBILITY, _("Mobility")),
    (OFFICE, _("Office")),
    (OTHER, _("Other")),
    (OTHER_HELP, _("Other help")),
    (SERVICE, _("Service")),
    (SHELTER, _("Shelter")),
    (SHOPPING, _("Shopping")),
    (STRUCTURE, _("Structure")),
]
