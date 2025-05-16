from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0125_add_statistics_tutorial_seen_to_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="searchresultfeedback",
            name="is_automatically_send",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
