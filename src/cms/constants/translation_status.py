from django.utils.translation import ugettext_lazy as _

DATATYPE = int

UP_TO_DATE = 0
MISSING = 1
OUTDATED = 2

CHOICES = (
    (UP_TO_DATE, _("Translation up-to-date")),
    (MISSING, _("Translation missing")),
    (OUTDATED, _("Translation outdated")),
)
