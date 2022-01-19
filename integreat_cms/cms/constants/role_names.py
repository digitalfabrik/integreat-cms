"""
This module contains the possible names of roles to make them translatable.
"""
from django.utils.translation import ugettext_lazy as _


#: Region management
MANAGEMENT = "MANAGEMENT"
#: Content editor
EDITOR = "EDITOR"
#: Event manager
EVENT_MANAGER = "EVENT_MANAGER"

#: Choices for non-staff roles
ROLES = [
    (MANAGEMENT, _("Management")),
    (EDITOR, _("Editor")),
    (EVENT_MANAGER, _("Event manager")),
]

#: Municipality team
MUNICIPALITY_TEAM = "MUNICIPALITY_TEAM"
#: CMS team
CMS_TEAM = "CMS_TEAM"
#: App team
APP_TEAM = "APP_TEAM"
#: Promo team
MARKETING_TEAM = "MARKETING_TEAM"

#: Choices for staff roles
STAFF_ROLES = [
    (MUNICIPALITY_TEAM, _("Municipality team")),
    (CMS_TEAM, _("CMS team")),
    (APP_TEAM, _("App team")),
    (MARKETING_TEAM, _("Marketing team")),
]

#: Choices to use these constants in a database field
CHOICES = ROLES + STAFF_ROLES
