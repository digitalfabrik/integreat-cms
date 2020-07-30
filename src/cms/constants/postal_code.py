"""
This module contains all possible configurations of postal codes in offers.
This is needed when the postal code is placed inside the offer's url or api request data.

* ``NONE``: No postal code needed for this offer

* ``GET``: Append postal code to offer URL

* ``POST``: Add postal code to post parameters of the offer's api
"""
from django.utils.translation import ugettext_lazy as _


NONE = "NONE"
GET = "GET"
POST = "POST"

CHOICES = (
    (NONE, _("No")),
    (GET, _("Append postal code to URL")),
    (POST, _("Add postal code to post parameters")),
)
