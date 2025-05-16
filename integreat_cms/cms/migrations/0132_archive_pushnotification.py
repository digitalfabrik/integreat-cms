from django.apps.registry import Apps
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from integreat_cms.cms.constants import roles


def update_roles(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Update translation settings permissions

    :param apps: The configuration of installed applications
    """
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # Emit post-migrate signal to make sure the Permission objects are created before they can be assigned
    emit_post_migrate_signal(2, False, "default")

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
    dependencies = [
        ("cms", "0131_add_automatical_feedback_to_searchresultfeedback"),
    ]

    operations = [
        migrations.AddField(
            model_name="pushnotification",
            name="archived",
            field=models.BooleanField(
                default=False,
                help_text="Whether or not the push notification is read-only and hidden in the API.",
                verbose_name="archived",
            ),
        ),
        migrations.AlterModelOptions(
            name="pushnotification",
            options={
                "default_permissions": ("change", "delete", "view", "archive"),
                "ordering": ["-created_date"],
                "permissions": (
                    ("send_push_notification", "Can send push notification"),
                ),
                "verbose_name": "push notification",
                "verbose_name_plural": "push notifications",
            },
        ),
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ]
