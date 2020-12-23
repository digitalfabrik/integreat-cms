"""
This module contains all constants representing the emotion of the :class:`~cms.models.feedback.feedback.Feedback` model.
"""
from django.utils.translation import ugettext_lazy as _


#: Positive
POS = "POS"
#: Negative
NEG = "NEG"
#: Not Available
NA = "NA"

#: Choices to use these constants in a database field
CHOICES = (
    (POS, _("Positive")),
    (NEG, _("Negative")),
    (NA, _("Not Available")),
)
