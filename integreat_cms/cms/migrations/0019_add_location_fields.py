# Generated by Django 3.2.13 on 2022-04-30 12:57

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add new fields to the POI/location model
    """

    dependencies = [
        ("cms", "0018_alter_location_coordinates"),
    ]

    operations = [
        migrations.AddField(
            model_name="poi",
            name="email",
            field=models.EmailField(
                blank=True,
                max_length=254,
                verbose_name="email address",
            ),
        ),
        migrations.AddField(
            model_name="poi",
            name="phone_number",
            field=models.CharField(
                blank=True,
                max_length=250,
                verbose_name="phone number",
            ),
        ),
        migrations.AddField(
            model_name="poi",
            name="website",
            field=models.URLField(blank=True, max_length=250, verbose_name="website"),
        ),
    ]
