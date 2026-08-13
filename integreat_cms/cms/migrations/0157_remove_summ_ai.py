from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def reset_summ_ai_provider(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    # Fall back to the default provider for language nodes which still prefer SUMM.AI
    LanguageTreeNode = apps.get_model("cms", "LanguageTreeNode")
    LanguageTreeNode.objects.filter(preferred_mt_provider="SUMM.AI").update(
        preferred_mt_provider="DeepL",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0156_remove_region_chat_enabled"),
    ]

    operations = [
        migrations.RunPython(reset_summ_ai_provider, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="region",
            name="summ_ai_budget_used",
        ),
        migrations.RemoveField(
            model_name="region",
            name="summ_ai_enabled",
        ),
        migrations.RemoveField(
            model_name="region",
            name="summ_ai_midyear_start_month",
        ),
        migrations.RemoveField(
            model_name="region",
            name="summ_ai_renewal_month",
        ),
        migrations.AlterField(
            model_name="languagetreenode",
            name="preferred_mt_provider",
            field=models.CharField(
                choices=[
                    ("DeepL", "DeepL"),
                    ("Google Translate", "Google Translate"),
                ],
                default="DeepL",
                help_text="Preferred provider for translations into this language",
                max_length=255,
                verbose_name="machine translation provider",
            ),
        ),
    ]
