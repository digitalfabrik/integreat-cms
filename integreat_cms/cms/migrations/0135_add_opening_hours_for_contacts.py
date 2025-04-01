from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0134_alter_region_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="appointment_url",
            field=models.URLField(
                blank=True,
                help_text="Link to an external website where an appointment for this contact can be made.",
                max_length=500,
                verbose_name="appointment link",
            ),
        ),
        migrations.AddField(
            model_name="contact",
            name="opening_hours",
            field=models.JSONField(blank=True, null=True, verbose_name="opening hours"),
        ),
    ]
