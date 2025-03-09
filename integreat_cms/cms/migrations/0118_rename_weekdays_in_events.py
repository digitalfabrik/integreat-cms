from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0117_add_beta_permission"),
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
