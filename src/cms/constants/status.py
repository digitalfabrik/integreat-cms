"""
This module contains the possible status of translations:

* ``DRAFT``: Draft

* ``REVIEW``: Pending Review

* ``PUBLIC``: Public
"""
from django.utils.translation import ugettext_lazy as _


DRAFT = 'DRAFT'
REVIEW = 'REVIEW'
PUBLIC = 'PUBLIC'

CHOICES = (
    (DRAFT, _('Draft')),
    (REVIEW, _('Pending Review')),
    (PUBLIC, _('Public')),
)
