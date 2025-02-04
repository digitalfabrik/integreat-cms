# Generated by Django 4.2.13 on 2024-06-09 21:21

import django.db.models.deletion
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
    Add permissions for managing external calendars

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
    Adds the external calendar model and related functionality to other models
    """

    dependencies = [
        ("cms", "0100_organization_archived"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="external_event_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="The ID of this event in the external calendar",
            ),
        ),
        migrations.CreateModel(
            name="ExternalCalendar",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        default="",
                        max_length=255,
                        verbose_name="calendar name",
                    ),
                ),
                (
                    "url",
                    models.URLField(max_length=250, verbose_name="URL"),
                ),
                (
                    "import_filter_category",
                    models.CharField(
                        blank=True,
                        default="integreat",
                        max_length=255,
                        verbose_name="The category that events need to have to get imported (Leave blank to import all events)",
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cms.region",
                        verbose_name="region",
                        related_name="external_calendars",
                    ),
                ),
                (
                    "errors",
                    models.CharField(
                        blank=True,
                        default="",
                        verbose_name="import errors",
                    ),
                ),
            ],
            options={
                "verbose_name": "external calendar",
                "verbose_name_plural": "external calendars",
                "default_permissions": ("change", "delete", "view"),
            },
        ),
        migrations.AddField(
            model_name="event",
            name="external_calendar",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to="cms.externalcalendar",
                verbose_name="external calendar",
            ),
        ),
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ]
