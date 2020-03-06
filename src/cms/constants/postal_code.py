from django.utils.translation import ugettext_lazy as _


NONE = 'NONE'
GET = 'GET'
POST = 'POST'

CHOICES = (
    (NONE, _('No')),
    (GET, _('Append postal code to URL')),
    (POST, _('Add postal code to post parameters')),
)
