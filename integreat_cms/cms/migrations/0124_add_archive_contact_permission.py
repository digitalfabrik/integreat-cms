from __future__ import annotations

from typing import TYPE_CHECKING

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
    Update the permission settings for the model contact

    :param apps: The configuration of installed applications
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
            *Permission.objects.filter(codename__in=roles.PERMISSIONS[role_name]),
        )


class Migration(migrations.Migration):
    """
    Migration file to update contact permissions
    """

    dependencies = [
        ("cms", "0123_allow_svg_uploads"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="contact",
            options={
                "default_permissions": ("change", "delete", "view", "archive"),
                "default_related_name": "contact",
                "ordering": ["location", "name"],
                "verbose_name": "contact",
                "verbose_name_plural": "contacts",
            },
        ),
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ]
