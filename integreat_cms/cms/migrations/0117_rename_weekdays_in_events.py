from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0116_remove_poi_email_remove_poi_phone_number_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="only_weekdays",
            field=models.BooleanField(
                default=False,
                help_text="Tick if this event takes place only on Monday through Friday",
                verbose_name="Only Mondays to Fridays",
            ),
        ),
    ]
