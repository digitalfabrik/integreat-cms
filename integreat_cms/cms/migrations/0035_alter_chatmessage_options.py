# Generated by Django 3.2.15 on 2022-08-26 12:09

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations

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


class Migration(migrations.Migration):
    """
    Update chat permission field to include default change permission.
    """

    dependencies = [
        ("cms", "0034_organization_region"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="chatmessage",
            options={
                "default_permissions": ("delete", "change"),
                "ordering": ["-sent_datetime"],
                "verbose_name": "chat message",
                "verbose_name_plural": "chat messages",
            },
        ),
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ]
