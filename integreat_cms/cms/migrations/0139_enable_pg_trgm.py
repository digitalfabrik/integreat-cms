from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0138_configurable_mt_budget"),
    ]

    operations = [
        TrigramExtension(),
    ]
