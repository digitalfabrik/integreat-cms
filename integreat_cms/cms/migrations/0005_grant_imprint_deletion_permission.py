# Generated by Django 3.2.11 on 2022-01-16 00:05
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def add_roles(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Add the default roles for users

    :param apps: The configuration of installed applications
    """
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    management_group = Group.objects.get(name="MANAGEMENT")
    delete_imprint_permission = Permission.objects.get(codename="delete_imprintpage")
    management_group.permissions.add(delete_imprint_permission)


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
    Permission = apps.get_model("auth", "Permission")

    management_group = Group.objects.get(name="MANAGEMENT")
    delete_imprint_permission = Permission.objects.get(codename="delete_imprintpage")
    management_group.permissions.remove(delete_imprint_permission)


class Migration(migrations.Migration):
    """
    Migration file to grant the imprint deletion permission to the management role
    """

    dependencies = [
        ("cms", "0004_alter_model_ordering"),
    ]

    operations = [
        migrations.RunPython(add_roles, remove_roles),
    ]
