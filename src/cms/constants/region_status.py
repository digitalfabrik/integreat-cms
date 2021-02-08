"""
This module contains the possible status of regions.
"""
from django.utils.translation import ugettext_lazy as _


#: Active
ACTIVE = "ACTIVE"
#: Hidden
HIDDEN = "HIDDEN"
#: Archived
ARCHIVED = "ARCHIVED"

#: Choices to use these constants in a database field
CHOICES = (
    (ACTIVE, _("Active")),
    (HIDDEN, _("Hidden")),
    (ARCHIVED, _("Archived")),
)
