from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0122_add_do_not_translate_title_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="opening_hours",
            field=models.JSONField(
                blank=True,
                help_text="These are the opening hours of the linked location.",
                null=True,
                verbose_name="opening hours",
            ),
        ),
    ]
