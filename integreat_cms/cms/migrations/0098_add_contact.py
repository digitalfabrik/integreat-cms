import django.db.models.deletion
import django.utils.timezone
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
    Initial migration file for contact
    """

    dependencies = [
        ("cms", "0097_alter_pushnotificationtranslation_text"),
    ]

    operations = [
        migrations.CreateModel(
            name="Contact",
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
                ("title", models.CharField(max_length=200, verbose_name="title")),
                ("name", models.CharField(max_length=200, verbose_name="name")),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        max_length=254,
                        verbose_name="email address",
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        blank=True,
                        max_length=250,
                        verbose_name="phone number",
                    ),
                ),
                (
                    "website",
                    models.URLField(blank=True, max_length=250, verbose_name="website"),
                ),
                (
                    "archived",
                    models.BooleanField(
                        default=False,
                        help_text="Whether or not the location is read-only and hidden in the API.",
                        verbose_name="archived",
                    ),
                ),
                (
                    "last_updated",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="modification date",
                    ),
                ),
                (
                    "created_date",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="creation date",
                    ),
                ),
                (
                    "poi",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="cms.poi",
                        verbose_name="POI",
                    ),
                ),
            ],
            options={
                "verbose_name": "contact",
                "verbose_name_plural": "contacts",
                "ordering": ["name"],
                "default_permissions": ("change", "delete", "view"),
                "default_related_name": "contact",
            },
        ),
    ]
