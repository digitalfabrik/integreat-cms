# Generated by Django 3.2.18 on 2023-05-01 18:20

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    """
    Rename key field for consistency reasons.
    """

    dependencies = [
        ("cms", "0077_adjust_region_deepl_addon_booked"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="UserMfaKey",
            new_name="FidoKey",
        ),
    ]
