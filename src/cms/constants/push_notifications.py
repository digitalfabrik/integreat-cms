"""
This module contains the possible modes for push notifications:

* ``ONLY_AVAILABLE``: Send only available translations
* ``USE_MAIN_LANGUAGE``: Use main language if no translation is available
"""
from django.utils.translation import ugettext_lazy as _


ONLY_AVAILABLE = "ONLY_AVAILABLE"
USE_MAIN_LANGUAGE = "USE_MAIN_LANGUAGE"

PN_MODES = (
    (ONLY_AVAILABLE, _("Only send available translations")),
    (USE_MAIN_LANGUAGE, _("Use main language if no translation is available")),
)
