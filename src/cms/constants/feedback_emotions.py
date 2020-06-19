"""
This module contains all constants representing the emotion of the :class:`~cms.models.feedback.feedback.Feedback` model:

* ``POS``: Positive

* ``NEG``: Negative

* ``NA``: Not Available
"""

from django.utils.translation import ugettext_lazy as _


POS = 'POS'
NEG = 'NEG'
NA = 'NA'

CHOICES = (
    (POS, _('Positive')),
    (NEG, _('Negative')),
    (NA, _('Not Available')),
)
