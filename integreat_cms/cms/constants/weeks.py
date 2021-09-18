"""
This module contains all string representations of a month's week, used by :class:`~integreat_cms.cms.models.events.event.Event`.
"""
from django.utils.translation import ugettext_lazy as _


#: First week of the month
FIRST = 1
#: Second week of the month
SECOND = 2
#: Third week of the month
THIRD = 3
#: Fourth week of the month
FOURTH = 4

#: Choices to use these constants in a database field
CHOICES = (
    (FIRST, _("First week")),
    (SECOND, _("Second week")),
    (THIRD, _("Third week")),
    (FOURTH, _("Fourth week")),
)
