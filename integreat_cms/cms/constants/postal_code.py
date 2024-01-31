"""
This module contains all possible configurations of postal codes in offers.
This is needed when the postal code is placed inside the offer's url or api request data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: No postal code needed for this offer
NONE: Final = "NONE"
#: Append postal code to offer URL
GET: Final = "GET"
#: Add postal code to post parameters of the offer's api
POST: Final = "POST"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (NONE, _("Do not use postcode")),
    (GET, _("Append postal code to URL")),
    (POST, _("Add postal code to post parameters")),
]
