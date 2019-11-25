from django.utils.translation import ugettext_lazy as _


MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6

CHOICES = (
    (MONDAY, _('Monday')),
    (TUESDAY, _('Tuesday')),
    (WEDNESDAY, _('Wednesday')),
    (THURSDAY, _('Thursday')),
    (FRIDAY, _('Friday')),
    (SATURDAY, _('Saturday')),
    (SUNDAY, _('Sunday'))
)
