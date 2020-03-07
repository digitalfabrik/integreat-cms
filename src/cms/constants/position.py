from django.utils.translation import ugettext_lazy as _


FIRST_CHILD = 'first-child'
LAST_CHILD = 'last-child'
LEFT = 'left'
RIGHT = 'right'

CHOICES = (
    (FIRST_CHILD, _('First child of')),
    (LAST_CHILD, _('Last child of')),
    (LEFT, _('Left neighbor of')),
    (RIGHT, _('Right neighbor of'))
    )
