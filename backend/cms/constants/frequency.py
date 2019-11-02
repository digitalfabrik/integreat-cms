from django.utils.translation import ugettext_lazy as _


DAILY = 'DAILY'
WEEKLY = 'WEEKLY'
MONTHLY = 'MONTHLY'
YEARLY = 'YEARLY'

CHOICES = (
    (DAILY, _('Daily')),
    (WEEKLY, _('Weekly')),
    (MONTHLY, _('Monthly')),
    (YEARLY, _('Yearly'))
)
