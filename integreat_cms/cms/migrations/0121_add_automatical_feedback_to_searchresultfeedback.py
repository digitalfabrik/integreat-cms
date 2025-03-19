from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0120_remove_fax_number_from_contact"),
    ]

    operations = [
        migrations.AddField(
            model_name="searchresultfeedback",
            name="is_automatically_send",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
