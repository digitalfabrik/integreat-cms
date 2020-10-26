"""
This module contains all constants representing the text directions of a :class:`~cms.models.languages.language.Language`:

* ``LTR``: Text is left to right, e.g. in English

* ``RTL``: Text is right to left, e.g. in Arabic
"""

from django.utils.translation import ugettext_lazy as _


LEFT_TO_RIGHT = "LEFT_TO_RIGHT"
RIGHT_TO_LEFT = "RIGHT_TO_LEFT"


CHOICES = (
    (LEFT_TO_RIGHT, _("Left to right")),
    (RIGHT_TO_LEFT, _("Right to left")),
)
