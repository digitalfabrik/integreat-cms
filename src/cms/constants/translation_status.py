from django.utils.translation import ugettext_lazy as _


UP_TO_DATE = "UP_TO_DATE"
IN_TRANSLATION = "IN_TRANSLATION"
OUTDATED = "OUTDATED"
MISSING = "MISSING"

CHOICES = (
    (UP_TO_DATE, _("Translation up-to-date")),
    (IN_TRANSLATION, _("Currently in translation")),
    (OUTDATED, _("Translation outdated")),
    (MISSING, _("Translation missing")),
)

COLORS = {
    UP_TO_DATE: "#4ade80",
    IN_TRANSLATION: "#60a5fa",
    OUTDATED: "#facc15",
    MISSING: "#f87171",
}
