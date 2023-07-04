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

ADVICE = "advice"
CULTURE = "culture"
DAILY_ROUTINE = "daily_routine"
EDUCATION = "education"
FINANCE = "finance"
GASTRONOMY = "gastronomy"
HEALTH = "health"
HOUSE = "house"
LEISURE = "leisure"
MEDIA = "media"
MEDICAL_AID = "medical_aid"
MEETING_POINT = "meeting_point"
MOBILITY = "mobility"
OFFICE = "office"
OTHER = "other"
OTHER_HELP = "other_help"
SERVICE = "service"
SHOPPING = "shopping"
STRUCTURE = "structure"

ICONS = [
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
    (MOBILITY, _("Mobility")),
    (OFFICE, _("Office")),
    (OTHER, _("Other")),
    (OTHER_HELP, _("Other help")),
    (SERVICE, _("Service")),
    (SHOPPING, _("Shopping")),
    (STRUCTURE, _("Structure")),
]
