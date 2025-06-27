from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations, models

from ..constants import machine_translation_budget

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def migrate_mt_addon_booked(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Transfer booked add-on package to MT budget L menu

    :param apps: The configuration of installed applications
    """
    Region = apps.get_model("cms", "Region")
    regions = Region.objects.all()

    for region in regions:
        region.mt_budget_booked = machine_translation_budget.MINIMAL
        if region.mt_addon_booked:
            region.mt_budget_booked = machine_translation_budget.LARGE
        region.save()


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0137_alter_pageaccesses_access_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="region",
            name="mt_budget_booked",
            field=models.PositiveIntegerField(
                choices=[
                    (50000, "50.000"),
                    (100000, "100.000"),
                    (150000, "150.000"),
                    (250000, "250.000"),
                    (1000000, "1.000.000"),
                    (5000000, "5.000.000"),
                ],
                default=50000,
                verbose_name="Machine translation budget",
            ),
        ),
        migrations.RunPython(migrate_mt_addon_booked, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="region",
            name="mt_addon_booked",
        ),
    ]
