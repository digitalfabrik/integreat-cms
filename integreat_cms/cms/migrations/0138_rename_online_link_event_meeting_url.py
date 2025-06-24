from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0137_alter_pageaccesses_access_date"),
    ]

    operations = [
        migrations.RenameField(
            model_name="event",
            old_name="online_link",
            new_name="meeting_url",
        ),
    ]
