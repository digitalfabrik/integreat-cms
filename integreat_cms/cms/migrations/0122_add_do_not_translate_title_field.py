from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0121_remove_userchat_most_recent_hits_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="do_not_translate_title",
            field=models.BooleanField(
                default=False,
                help_text="Tick if you do not want to translate the title by automatic translation.",
                verbose_name="do not translate the title",
            ),
        ),
        migrations.AddField(
            model_name="imprintpage",
            name="do_not_translate_title",
            field=models.BooleanField(
                default=False,
                help_text="Tick if you do not want to translate the title by automatic translation.",
                verbose_name="do not translate the title",
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="do_not_translate_title",
            field=models.BooleanField(
                default=False,
                help_text="Tick if you do not want to translate the title by automatic translation.",
                verbose_name="do not translate the title",
            ),
        ),
        migrations.AddField(
            model_name="poi",
            name="do_not_translate_title",
            field=models.BooleanField(
                default=False,
                help_text="Tick if you do not want to translate the title by automatic translation.",
                verbose_name="do not translate the title",
            ),
        ),
    ]
