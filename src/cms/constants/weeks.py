"""
This module contains all string representations of a month's week, used by :class:`~cms.models.events.event.Event`:

* ``FIRST``: First week of the month

* ``SECOND``: Second week of the month

* ``THIRD``: Third week of the month

* ``FOURTH``: Fourth week of the month
"""
from django.utils.translation import ugettext_lazy as _


FIRST = 1
SECOND = 2
THIRD = 3
FOURTH = 4

CHOICES = (
    (FIRST, _("First week")),
    (SECOND, _("Second week")),
    (THIRD, _("Third week")),
    (FOURTH, _("Fourth week")),
)
