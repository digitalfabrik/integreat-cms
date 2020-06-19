"""
This module contains all constants representing the text directions of a :class:`~cms.models.languages.language.Language`:

* ``LTR``: Text is left to right, e.g. in English

* ``RTL``: Text is right to left, e.g. in Arabic
"""

from django.utils.translation import ugettext_lazy as _


LTR = 'LTR'
RTL = 'RTL'


CHOICES = (
    (LTR, _('Left to right')),
    (RTL, _('Right to left')),
)
