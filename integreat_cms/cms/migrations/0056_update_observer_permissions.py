from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations

from ..constants import roles

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


# pylint: disable=unused-argument
def update_roles(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """
    Update the role definitions

    :param apps: The configuration of installed applications
    :param schema_editor: The database abstraction layer that creates actual SQL code
    """
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # Assign the correct permissions
    for role_name in dict(roles.CHOICES):
        group, _ = Group.objects.get_or_create(name=role_name)
        # Clear permissions
        group.permissions.clear()
        # Set permissions
        group.permissions.add(
            *Permission.objects.filter(codename__in=roles.PERMISSIONS[role_name])
        )


class Migration(migrations.Migration):
    """
    Migration file to update permissions of observer
    """

    dependencies = [
        ("cms", "0055_track_region_deepl_api_usage"),
    ]

    operations = [
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ]
