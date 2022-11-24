"""
This module contains the possible modes for push notifications.
"""
from django.utils.translation import gettext_lazy as _


#: Send only available translations
ONLY_AVAILABLE = "ONLY_AVAILABLE"
#: Use main language if no translation is available
USE_MAIN_LANGUAGE = "USE_MAIN_LANGUAGE"

#: Choices to use these constants in a database field
PN_MODES = (
    (ONLY_AVAILABLE, _("Only send available translations")),
    (USE_MAIN_LANGUAGE, _("Use main language if no translation is available")),
)
