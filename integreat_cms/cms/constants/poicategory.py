"""
This module contains constants for POICategory.
"""
from django.utils.translation import gettext_lazy as _

DARK_BLUE = "#3700D2"
SKY_BLUE = "#2E98FB"
CYAN = "#1DC6C6"
FOREST_GREEN = "#3F8F01"
LAWN_GREEN = "#07DC03"
YELLOW = "#F2DA04"
GOLD = "#C38E03"
ORANGE = "#FF7C32"
RED = "#FF3333"
PINK = "#EE36DC"
LAVENDER = "#A258FF"
GREY = "#585858"

COLORS = [
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

CULTURE = "culture"
GASTRONOMY = "gastronomy"
HEALTH = "health"
HOUSE = "house"
LEISURE = "leisure"
MEDIA = "media"
MEETING_POINT = "meeting_point"
MOBILITY = "mobility"
OFFICE = "office"
OTHER = "other"
SERVICE = "service"
SHOPPING = "shopping"

ICONS = [
    (CULTURE, _("Culture")),
    (GASTRONOMY, _("Gastronomy")),
    (HEALTH, _("Health")),
    (HOUSE, _("House")),
    (LEISURE, _("Leisure")),
    (MEDIA, _("Media")),
    (MEETING_POINT, _("Meeting point")),
    (MOBILITY, _("Mobility")),
    (OFFICE, _("Office")),
    (OTHER, _("Other")),
    (SERVICE, _("Service")),
    (SHOPPING, _("Shopping")),
]
