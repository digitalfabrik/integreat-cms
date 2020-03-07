from django.utils.translation import ugettext_lazy as _


ACTIVE = 'ACTIVE'
HIDDEN = 'HIDDEN'
ARCHIVED = 'ARCHIVED'

CHOICES = (
    (ACTIVE, _('Active')),
    (HIDDEN, _('Hidden')),
    (ARCHIVED, _('Archived')),
)
