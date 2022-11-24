"""
This module contains all possible configurations of postal codes in offers.
This is needed when the postal code is placed inside the offer's url or api request data.
"""
from django.utils.translation import gettext_lazy as _


#: No postal code needed for this offer
NONE = "NONE"
#: Append postal code to offer URL
GET = "GET"
#: Add postal code to post parameters of the offer's api
POST = "POST"

#: Choices to use these constants in a database field
CHOICES = (
    (NONE, _("Do not use postcode")),
    (GET, _("Append postal code to URL")),
    (POST, _("Add postal code to post parameters")),
)
