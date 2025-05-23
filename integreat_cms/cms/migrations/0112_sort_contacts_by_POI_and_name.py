# Generated by Django 4.2.16 on 2025-01-13 12:40

from django.db import migrations


class Migration(migrations.Migration):
    """
    Sort contacts first by POI and then name
    """

    dependencies = [
        ("cms", "0111_alter_language_language_color"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="contact",
            options={
                "default_permissions": ("change", "delete", "view"),
                "default_related_name": "contact",
                "ordering": ["location", "name"],
                "verbose_name": "contact",
                "verbose_name_plural": "contacts",
            },
        ),
    ]
