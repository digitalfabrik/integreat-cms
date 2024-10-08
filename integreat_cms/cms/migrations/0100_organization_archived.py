# Generated by Django 4.2.13 on 2024-08-04 16:01

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add field for archiving an organization.
    """

    dependencies = [
        ("cms", "0099_firebasestatistic"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="archived",
            field=models.BooleanField(default=False, verbose_name="archived"),
        ),
    ]
