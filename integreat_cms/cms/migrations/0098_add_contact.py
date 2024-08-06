import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


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
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        blank=True, max_length=250, verbose_name="phone number"
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
                        auto_now=True, verbose_name="modification date"
                    ),
                ),
                (
                    "created_date",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="creation date"
                    ),
                ),
                (
                    "poi",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cms.poi",
                        verbose_name="POI",
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cms.region",
                        verbose_name="region",
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
