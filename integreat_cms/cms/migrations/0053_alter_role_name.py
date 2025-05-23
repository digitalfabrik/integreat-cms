# Generated by Django 3.2.16 on 2022-11-18 13:36

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models

from ..constants import roles

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def update_roles(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Update permissions for service and management group

    :param apps: The configuration of installed applications
    """
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    Role = apps.get_model("cms", "Role")

    # Emit post-migrate signal to make sure the Permission objects are created before they can be assigned
    emit_post_migrate_signal(2, False, "default")

    # Clear and update permissions according to new constants
    for role_name in dict(roles.CHOICES):
        group, _ = Group.objects.get_or_create(name=role_name)
        # Clear permissions
        group.permissions.clear()
        # Set permissions
        group.permissions.add(
            *Permission.objects.filter(codename__in=roles.PERMISSIONS[role_name]),
        )

    # Create the new role Observer
    observer, _ = Group.objects.get_or_create(name="OBSERVER")
    Role.objects.get_or_create(name="OBSERVER", group=observer)


class Migration(migrations.Migration):
    """
    Add a new role without editing permission
    """

    dependencies = [
        ("cms", "0052_alter_poi_icon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="role",
            name="name",
            field=models.CharField(
                choices=[
                    ("MANAGEMENT", "Manager"),
                    ("EDITOR", "Editor"),
                    ("AUTHOR", "Author"),
                    ("EVENT_MANAGER", "Event manager"),
                    ("OBSERVER", "Observer"),
                    ("SERVICE_TEAM", "Service team"),
                    ("CMS_TEAM", "CMS team"),
                    ("APP_TEAM", "App team"),
                    ("MARKETING_TEAM", "Marketing team"),
                ],
                max_length=50,
                verbose_name="name",
            ),
        ),
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ]
