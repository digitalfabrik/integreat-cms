"""
This module contains all constants representing the text directions of a :class:`~integreat_cms.cms.models.languages.language.Language`.
"""
from django.utils.translation import gettext_lazy as _


#: Text is left to right, e.g. in English
LEFT_TO_RIGHT = "LEFT_TO_RIGHT"
#: Text is right to left, e.g. in Arabic
RIGHT_TO_LEFT = "RIGHT_TO_LEFT"

#: Choices to use these constants in a database field
CHOICES = (
    (LEFT_TO_RIGHT, _("Left to right")),
    (RIGHT_TO_LEFT, _("Right to left")),
)
