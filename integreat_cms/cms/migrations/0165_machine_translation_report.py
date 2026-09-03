import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0164_add_currently_in_machine_translation_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="MachineTranslationReport",
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
                    "content_type",
                    models.CharField(max_length=20, verbose_name="content type"),
                ),
                (
                    "language_slugs",
                    models.JSONField(verbose_name="target language slugs"),
                ),
                (
                    "results",
                    models.JSONField(verbose_name="per-language, per-object results"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation date"
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="machine_translation_reports",
                        to="cms.region",
                        verbose_name="region",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="machine_translation_reports",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "machine translation report",
                "verbose_name_plural": "machine translation reports",
                "ordering": ["created_at"],
                "default_permissions": (),
            },
        ),
        migrations.AddIndex(
            model_name="machinetranslationreport",
            index=models.Index(
                fields=["user", "region", "content_type"],
                name="cms_machine_user_id_5a3b40_idx",
            ),
        ),
    ]
