# Generated by Django 3.2.11 on 2022-01-16 00:05
from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor

ROLES = [
    {
        "name": "MANAGEMENT",
        "staff_role": False,
        "permissions": [
            "add_directory",
            "change_directory",
            "delete_directory",
            "view_directory",
            "change_event",
            "publish_event",
            "view_event",
            "change_feedback",
            "delete_feedback",
            "view_feedback",
            "change_imprintpage",
            "view_imprintpage",
            "change_mediafile",
            "delete_mediafile",
            "replace_mediafile",
            "upload_mediafile",
            "view_mediafile",
            "change_page",
            "grant_page_permissions",
            "publish_page",
            "view_page",
            "change_poi",
            "view_poi",
            "change_pushnotification",
            "send_push_notification",
            "view_pushnotification",
            "change_user",
            "view_user",
        ],
    },
    {
        "name": "EDITOR",
        "staff_role": False,
        "permissions": [
            "add_directory",
            "change_directory",
            "view_directory",
            "change_event",
            "view_event",
            "change_feedback",
            "view_feedback",
            "change_imprintpage",
            "view_imprintpage",
            "change_mediafile",
            "delete_mediafile",
            "replace_mediafile",
            "upload_mediafile",
            "view_mediafile",
            "change_page",
            "view_page",
            "change_poi",
            "view_poi",
        ],
    },
    {
        "name": "EVENT_MANAGER",
        "staff_role": False,
        "permissions": [
            "add_directory",
            "change_directory",
            "view_directory",
            "change_event",
            "publish_event",
            "view_event",
            "change_feedback",
            "view_feedback",
            "view_imprintpage",
            "change_mediafile",
            "delete_mediafile",
            "replace_mediafile",
            "upload_mediafile",
            "view_mediafile",
            "change_poi",
            "view_poi",
        ],
    },
    {
        "name": "MUNICIPALITY_TEAM",
        "staff_role": True,
        "permissions": [
            "delete_chatmessage",
            "add_directory",
            "change_directory",
            "delete_directory",
            "view_directory",
            "change_event",
            "delete_event",
            "publish_event",
            "view_event",
            "change_feedback",
            "delete_feedback",
            "view_feedback",
            "change_imprintpage",
            "delete_imprintpage",
            "view_imprintpage",
            "change_language",
            "view_language",
            "change_languagetreenode",
            "delete_languagetreenode",
            "view_languagetreenode",
            "change_mediafile",
            "delete_mediafile",
            "replace_mediafile",
            "upload_mediafile",
            "view_mediafile",
            "change_offertemplate",
            "delete_offertemplate",
            "view_offertemplate",
            "change_organization",
            "view_organization",
            "change_page",
            "delete_page",
            "grant_page_permissions",
            "publish_page",
            "view_page",
            "change_poi",
            "delete_poi",
            "view_poi",
            "change_pushnotification",
            "send_push_notification",
            "view_pushnotification",
            "change_region",
            "view_region",
            "change_user",
            "delete_user",
            "view_user",
        ],
    },
    {
        "name": "CMS_TEAM",
        "staff_role": True,
        "permissions": [
            "delete_chatmessage",
            "add_directory",
            "change_directory",
            "delete_directory",
            "view_directory",
            "change_event",
            "delete_event",
            "publish_event",
            "view_event",
            "change_feedback",
            "delete_feedback",
            "view_feedback",
            "change_imprintpage",
            "delete_imprintpage",
            "view_imprintpage",
            "change_language",
            "view_language",
            "change_languagetreenode",
            "delete_languagetreenode",
            "view_languagetreenode",
            "change_mediafile",
            "delete_mediafile",
            "replace_mediafile",
            "upload_mediafile",
            "view_mediafile",
            "change_offertemplate",
            "view_offertemplate",
            "change_organization",
            "view_organization",
            "change_page",
            "grant_page_permissions",
            "publish_page",
            "view_page",
            "change_poi",
            "view_poi",
            "change_pushnotification",
            "send_push_notification",
            "view_pushnotification",
            "change_region",
            "view_region",
            "change_user",
            "view_user",
        ],
    },
    {
        "name": "APP_TEAM",
        "staff_role": True,
        "permissions": [
            "view_directory",
            "view_event",
            "change_feedback",
            "view_feedback",
            "view_imprintpage",
            "view_language",
            "view_languagetreenode",
            "view_mediafile",
            "view_offertemplate",
            "view_organization",
            "view_page",
            "view_poi",
            "view_pushnotification",
            "view_region",
            "view_user",
        ],
    },
    {
        "name": "MARKETING_TEAM",
        "staff_role": True,
        "permissions": [
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
            "view_pushnotification",
            "view_region",
            "view_user",
        ],
    },
]


def add_roles(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Add the default roles for users

    :param apps: The configuration of installed applications
    """
    # Emit post-migrate signal to make sure the Permission objects are created before they can be assigned
    emit_post_migrate_signal(2, False, "default")

    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    Role = apps.get_model("cms", "Role")

    for role_conf in ROLES:
        group, _ = Group.objects.get_or_create(name=role_conf.get("name"))
        Role.objects.get_or_create(
            name=role_conf.get("name"),
            group=group,
            staff_role=role_conf.get("staff_role"),
        )
        permissions = Permission.objects.filter(
            codename__in=role_conf.get("permissions"),
        )
        group.permissions.add(*permissions)


def remove_roles(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Remove the default roles for users

    :param apps: The configuration of installed applications
    """
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Group = apps.get_model("auth", "Group")
    Role = apps.get_model("cms", "Role")

    for role_conf in ROLES:
        Group.objects.filter(name=role_conf.get("name")).delete()
        Role.objects.filter(name=role_conf.get("name")).delete()


class Migration(migrations.Migration):
    """
    Migration file to create the initial roles
    """

    dependencies = [
        ("cms", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_roles, remove_roles),
    ]
