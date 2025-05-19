import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Initial migration file for the Page Accesses model
    """

    dependencies = [
        ("cms", "0132_archive_pushnotification"),
    ]

    operations = [
        migrations.CreateModel(
            name="PageAccesses",
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
                    "access_date",
                    models.DateTimeField(verbose_name="Date of the page accesses"),
                ),
                (
                    "language",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        to="cms.language",
                        verbose_name="Languages of the page that was accessed",
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        to="cms.page",
                        verbose_name="Accessed page",
                    ),
                ),
                (
                    "accesses",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Page accesses",
                    ),
                ),
            ],
            options={
                "default_permissions": ("change", "delete", "view"),
                "default_related_name": "page_accesses",
                "ordering": ["pk"],
                "verbose_name": "page accesses",
                "verbose_name_plural": "page accesses",
            },
        ),
        migrations.AddConstraint(
            model_name="PageAccesses",
            constraint=models.UniqueConstraint(
                fields=("page", "language", "access_date"),
                name="pageaccesses_unique_version",
            ),
        ),
    ]
