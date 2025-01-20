from __future__ import annotations

import zoneinfo
from datetime import datetime
from typing import TYPE_CHECKING

from django.db import migrations, models
from django.utils import timezone

from ..constants import frequency

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def remove_end_date_from_existing_events(
    apps: Apps, _schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """
    Set the end date of existing events equal to start date, if they have recurrence rule.
    """
    Event = apps.get_model("cms", "Event")
    events = Event.objects.all()
    for event in events:
        if recurrence_rule := event.recurrence_rule:
            region_timezone = event.region.timezone
            timezone.activate(region_timezone)
            start = timezone.localtime(event.start)
            end = timezone.localtime(event.end)

            tzinfo = zoneinfo.ZoneInfo(region_timezone)
            if start.date() != end.date():
                if recurrence_rule.frequency != frequency.DAILY:
                    event.end = datetime.combine(start.date(), end.time()).replace(
                        tzinfo=tzinfo
                    )
                else:
                    event.recurrence_rule = None
                event.save()
                continue
            if (
                recurrence_rule.frequency == frequency.DAILY
                and recurrence_rule.recurrence_end_date
            ):
                event.end = datetime.combine(
                    recurrence_rule.recurrence_end_date, end.time()
                ).replace(tzinfo=tzinfo)
                event.recurrence_rule = None
                event.save()


class Migration(migrations.Migration):
    """
    Offer long-term events
    """

    dependencies = [
        ("cms", "0112_sort_contacts_by_POI_and_name"),
    ]

    operations = [
        migrations.RunPython(remove_end_date_from_existing_events),
        migrations.AlterField(
            model_name="event",
            name="end",
            field=models.DateTimeField(blank=True, verbose_name="end"),
        ),
        migrations.AddField(
            model_name="event",
            name="only_weekdays",
            field=models.BooleanField(
                default=False,
                help_text="Tick if this event takes place only on weekdays",
                verbose_name="Only weekdays",
            ),
        ),
    ]
