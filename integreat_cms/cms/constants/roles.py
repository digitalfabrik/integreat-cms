"""
This module contains the possible names of roles to make them translatable and the permission definitions.
"""
from django.utils.translation import ugettext_lazy as _


#: Region management
MANAGEMENT = "MANAGEMENT"
#: Content editor
EDITOR = "EDITOR"
#: Author
AUTHOR = "AUTHOR"
#: Event manager
EVENT_MANAGER = "EVENT_MANAGER"

#: Choices for non-staff roles
ROLES = [
    (MANAGEMENT, _("Manager")),
    (EDITOR, _("Editor")),
    (AUTHOR, _("Author")),
    (EVENT_MANAGER, _("Event manager")),
]

#: Service team
SERVICE_TEAM = "SERVICE_TEAM"
#: CMS team
CMS_TEAM = "CMS_TEAM"
#: App team
APP_TEAM = "APP_TEAM"
#: Promo team
MARKETING_TEAM = "MARKETING_TEAM"

#: Choices for staff roles
STAFF_ROLES = [
    (SERVICE_TEAM, _("Service team")),
    (CMS_TEAM, _("CMS team")),
    (APP_TEAM, _("App team")),
    (MARKETING_TEAM, _("Marketing team")),
]

#: Choices to use these constants in a database field
CHOICES = ROLES + STAFF_ROLES

#: The permissions of the event manager role
EVENT_MANAGER_PERMISSIONS = [
    "add_directory",
    "change_directory",
    "change_event",
    "change_mediafile",
    "change_poi",
    "publish_event",
    "replace_mediafile",
    "upload_mediafile",
    "view_directory",
    "view_event",
    "view_mediafile",
    "view_poi",
]

#: The permissions of the author role
AUTHOR_PERMISSIONS = EVENT_MANAGER_PERMISSIONS + [
    "change_page",
    "view_page",
]


#: The permissions of the editor role
EDITOR_PERMISSIONS = AUTHOR_PERMISSIONS + [
    "publish_page",
    "view_translation_report",
    "view_broken_links",
]

#: The permissions of the management role
MANAGEMENT_PERMISSIONS = EDITOR_PERMISSIONS + [
    "change_feedback",
    "change_imprintpage",
    "change_organization",
    "change_pushnotification",
    "change_user",
    "change_chatmessage",
    "delete_directory",
    "delete_feedback",
    "delete_mediafile",
    "delete_organization",
    "grant_page_permissions",
    "send_push_notification",
    "view_feedback",
    "view_imprintpage",
    "view_organization",
    "view_pushnotification",
    "view_user",
    "view_statistics",
]

#: The permissions of the marketing team
MARKETING_TEAM_PERMISSIONS = [
    "change_chatmessage",
    "view_directory",
    "view_event",
    "view_feedback",
    "view_imprintpage",
    "view_language",
    "view_languagetreenode",
    "view_mediafile",
    "view_offertemplate",
    "view_organization",
    "view_page",
    "view_poi",
    "view_poicategory",
    "view_pushnotification",
    "view_region",
    "view_user",
    "view_translation_report",
    "view_broken_links",
    "view_statistics",
]

#: The permissions of the app team
APP_TEAM_PERMISSIONS = MARKETING_TEAM_PERMISSIONS + [
    "add_directory",
    "change_directory",
    "change_event",
    "change_feedback",
    "change_imprintpage",
    "change_mediafile",
    "change_page",
    "change_poi",
    "change_pushnotification",
    "change_region",
    "delete_mediafile",
    "publish_event",
    "publish_page",
    "replace_mediafile",
    "send_push_notification",
    "upload_mediafile",
]

#: The permissions of the service team
SERVICE_TEAM_PERMISSIONS = APP_TEAM_PERMISSIONS + [
    "change_language",
    "change_languagetreenode",
    "change_offertemplate",
    "change_organization",
    "change_poicategory",
    "change_user",
    "delete_chatmessage",
    "delete_directory",
    "delete_event",
    "delete_feedback",
    "delete_imprintpage",
    "delete_languagetreenode",
    "delete_offertemplate",
    "delete_organization",
    "delete_page",
    "delete_poi",
    "delete_poicategory",
    "delete_pushnotification",
    "delete_region",
    "delete_user",
    "grant_page_permissions",
]

#: The permissions of the cms team
CMS_TEAM_PERMISSIONS = SERVICE_TEAM_PERMISSIONS

#: The permissions of all roles
PERMISSIONS = {
    EVENT_MANAGER: EVENT_MANAGER_PERMISSIONS,
    AUTHOR: AUTHOR_PERMISSIONS,
    EDITOR: EDITOR_PERMISSIONS,
    MANAGEMENT: MANAGEMENT_PERMISSIONS,
    MARKETING_TEAM: MARKETING_TEAM_PERMISSIONS,
    APP_TEAM: APP_TEAM_PERMISSIONS,
    SERVICE_TEAM: SERVICE_TEAM_PERMISSIONS,
    CMS_TEAM: CMS_TEAM_PERMISSIONS,
}
