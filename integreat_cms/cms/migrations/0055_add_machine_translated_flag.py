# Generated by Django 3.2.16 on 2022-12-19 10:15

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adding machine translated flag to models
    """

    dependencies = [
        ("cms", "0054_user_totp_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventtranslation",
            name="machine_translated",
            field=models.BooleanField(
                default=False,
                help_text="Flag to indicate whether a translations is machine translated",
                verbose_name="machine translated",
            ),
        ),
        migrations.AddField(
            model_name="imprintpagetranslation",
            name="machine_translated",
            field=models.BooleanField(
                default=False,
                help_text="Flag to indicate whether a translations is machine translated",
                verbose_name="machine translated",
            ),
        ),
        migrations.AddField(
            model_name="pagetranslation",
            name="machine_translated",
            field=models.BooleanField(
                default=False,
                help_text="Flag to indicate whether a translations is machine translated",
                verbose_name="machine translated",
            ),
        ),
        migrations.AddField(
            model_name="poitranslation",
            name="machine_translated",
            field=models.BooleanField(
                default=False,
                help_text="Flag to indicate whether a translations is machine translated",
                verbose_name="machine translated",
            ),
        ),
    ]