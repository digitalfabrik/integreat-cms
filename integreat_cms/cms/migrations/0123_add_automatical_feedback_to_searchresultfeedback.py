from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0122_add_do_not_translate_title_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="searchresultfeedback",
            name="is_automatically_send",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
