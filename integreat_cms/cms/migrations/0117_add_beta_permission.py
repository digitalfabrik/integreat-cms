from django.apps.registry import Apps
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from integreat_cms.cms.constants import roles


def update_roles(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Add permissions for testing beta features
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
    Migration file for adding permissions to test beta features
    """

    dependencies = [
        ("cms", "0116_remove_poi_email_remove_poi_phone_number_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "default_permissions": ("change", "delete", "view"),
                "ordering": ["username"],
                "permissions": (
                    ("view_translation_report", "view_translation_report"),
                    ("view_broken_links", "view_broken_links"),
                    ("view_statistics", "view_statistics"),
                    ("manage_translations", "manage_translations"),
                    ("test_beta_features", "test_beta_features"),
                ),
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ]
