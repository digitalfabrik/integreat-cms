# Generated by Django 3.2.14 on 2022-08-21 13:03
from __future__ import annotations

import zoneinfo
from datetime import datetime
from typing import TYPE_CHECKING

from django.db import migrations, models

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def start_and_end_init(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Initialize the new event datetime fields 'start' and 'end' from the respective
    existing fields *_date and *_time.

    :param apps: The configuration of installed applications
    """
    Event = apps.get_model("cms", "Event")
    for event in Event.objects.all():
        # Get the region's timezone instead of UTC
        tzinfo = zoneinfo.ZoneInfo(event.region.timezone)
        # Populate the new datetime fields by combining the previous date and time fields
        event.start = datetime.combine(event.start_date, event.start_time, tzinfo)
        event.end = datetime.combine(event.end_date, event.end_time, tzinfo)
        event.save()


def start_and_end_reverse(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Initialize the old event date and time fields from the respective new fields start and end.

    :param apps: The configuration of installed applications
    """
    Event = apps.get_model("cms", "Event")
    for event in Event.objects.all():
        # Populate the previous date and time fields with the new datetime fields
        event.start_date = event.start_local.date()
        event.start_time = event.start_local.time()
        event.end_date = event.end_local.date()
        event.end_time = event.end_local.time()
        event.save()


class Migration(migrations.Migration):
    """
    Update the datetime fields from the event model
    """

    dependencies = [
        ("cms", "0036_add_non_political_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="end",
            field=models.DateTimeField(null=True, verbose_name="end"),
        ),
        migrations.AddField(
            model_name="event",
            name="start",
            field=models.DateTimeField(null=True, verbose_name="start"),
        ),
        migrations.AlterModelOptions(
            name="event",
            options={
                "default_permissions": ("change", "delete", "view"),
                "default_related_name": "events",
                "ordering": ["start"],
                "permissions": (("publish_event", "Can publish events"),),
                "verbose_name": "event",
                "verbose_name_plural": "events",
            },
        ),
        migrations.RunPython(start_and_end_init, start_and_end_reverse),
        migrations.AlterField(
            model_name="event",
            name="end",
            field=models.DateTimeField(verbose_name="end"),
        ),
        migrations.AlterField(
            model_name="event",
            name="start",
            field=models.DateTimeField(verbose_name="start"),
        ),
        migrations.RemoveField(
            model_name="event",
            name="end_date",
        ),
        migrations.RemoveField(
            model_name="event",
            name="end_time",
        ),
        migrations.RemoveField(
            model_name="event",
            name="start_date",
        ),
        migrations.RemoveField(
            model_name="event",
            name="start_time",
        ),
    ]
