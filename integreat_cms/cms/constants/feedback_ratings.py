"""
This module contains all constants representing the rating of the :class:`~integreat_cms.cms.models.feedback.feedback.Feedback` model.
"""
from django.utils.translation import gettext_lazy as _


#: Positive
POSITIVE = True
#: Negative
NEGATIVE = False
#: Not stated
NOT_STATED = None
#: Not stated as string (used in the filter form)
NOT_STATED_STR = ""

#: Choices to use these constants in a database field
CHOICES = (
    (POSITIVE, _("Positive")),
    (NEGATIVE, _("Negative")),
    (NOT_STATED, _("Not stated")),
)

#: Choices for the filter form (required because ``None`` is always converted to ``""``)
FILTER_CHOICES = (
    (POSITIVE, _("Positive")),
    (NEGATIVE, _("Negative")),
    (NOT_STATED_STR, _("Not stated")),
)

#: Initial filter options
INITIAL = [key for (key, val) in FILTER_CHOICES]
