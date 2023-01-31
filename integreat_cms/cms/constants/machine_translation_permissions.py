"""
This module contains string representations of permission levels for machine
translations, used by :class:`~integreat_cms.cms.models.regions.region.Region`.
"""
from django.utils.translation import gettext_lazy as _


#: Machine Translations are disabled
NO_ONE = 0
#: Everyone can use Machine Translation
EVERYONE = 1
#: Only Managers can use Machine Translations
MANAGERS = 2

#: Choices to use these constants in a database field
CHOICES = (
    (NO_ONE, _("No")),
    (EVERYONE, _("Yes")),
    (MANAGERS, _("Yes, only managers")),
)
