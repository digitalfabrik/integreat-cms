from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations, models

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def convert_midyear_start_to_budget(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Convert the pro-rated budget of midyear-start regions into an equivalent booked budget

    The old ``mt_budget`` property multiplied the booked budget by the fraction of the budget year
    that was left when the add-on was booked. That pro-rating is replaced by an explicit
    adjustment, so the effective budget is written into ``mt_budget_booked`` once and the regions
    keep exactly the budget they have today.

    :param apps: The configuration of installed applications
    :param _schema_editor: The database abstraction layer that creates actual SQL code
    """
    Region = apps.get_model("cms", "Region")
    for region in Region.objects.filter(mt_midyear_start_month__isnull=False):
        months_difference = region.mt_renewal_month - region.mt_midyear_start_month
        multiplier = (months_difference % 12) / 12
        region.mt_budget_booked = int(multiplier * region.mt_budget_booked)
        region.save(update_fields=["mt_budget_booked"])


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0160_news_wording"),
    ]

    operations = [
        migrations.AddField(
            model_name="region",
            name="mt_budget_adjustment",
            field=models.IntegerField(
                blank=True,
                default=0,
                help_text="Cumulative manual adjustment for the current budget year, added on top of the booked budget. Negative values reduce the budget.",
                verbose_name="Machine translation budget adjustment",
            ),
        ),
        migrations.AddField(
            model_name="region",
            name="api_settings_synced_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Set when the region settings were last written through the API. Regions with a value here are managed externally and their synced settings are read-only in this form.",
                null=True,
                verbose_name="last settings sync via API",
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="mt_budget_booked",
            field=models.PositiveIntegerField(
                default=50000,
                help_text="The booked budget in number of words. For regions managed via the API this can be any value, so no choices are enforced on the model.",
                verbose_name="Machine translation budget",
            ),
        ),
        migrations.RunPython(
            convert_midyear_start_to_budget,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="region",
            name="mt_midyear_start_month",
        ),
    ]
