from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0157_remove_summ_ai"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventtranslation",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="imprintpagetranslation",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="pagetranslation",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="poitranslation",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
    ]
