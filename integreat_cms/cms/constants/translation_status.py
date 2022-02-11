"""
This module contains the states a translation can have
"""
from django.utils.translation import ugettext_lazy as _

#: Up to date
UP_TO_DATE = "UP_TO_DATE"
#: In translation
IN_TRANSLATION = "IN_TRANSLATION"
#: Outdated
OUTDATED = "OUTDATED"
#: Missing
MISSING = "MISSING"

#: Choices to use these constants in a database field
CHOICES = (
    (UP_TO_DATE, _("Translation up-to-date")),
    (IN_TRANSLATION, _("Currently in translation")),
    (OUTDATED, _("Translation outdated")),
    (MISSING, _("Translation missing")),
)

#: Maps from the translation state to the color used to render this state in the translation coverage view
COLORS = {
    UP_TO_DATE: "#4ade80",
    IN_TRANSLATION: "#60a5fa",
    OUTDATED: "#facc15",
    MISSING: "#f87171",
}
