"""
This module contains the possible status of regions:

* ``ACTIVE``: Active

* ``HIDDEN``: Hidden

* ``ARCHIVED``: Archived
"""
from django.utils.translation import ugettext_lazy as _


ACTIVE = 'ACTIVE'
HIDDEN = 'HIDDEN'
ARCHIVED = 'ARCHIVED'

CHOICES = (
    (ACTIVE, _('Active')),
    (HIDDEN, _('Hidden')),
    (ARCHIVED, _('Archived')),
)
