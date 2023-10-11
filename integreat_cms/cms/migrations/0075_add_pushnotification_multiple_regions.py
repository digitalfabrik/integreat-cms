from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations, models
from django.db.models.deletion import CASCADE

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


# pylint: disable=unused-argument
def forwards_func(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """
    Adopting the old data when applying this migration

    :param apps: The configuration of installed applications
    :param schema_editor: The database abstraction layer that creates actual SQL code
    """
    PushNotification = apps.get_model("cms", "PushNotification")
    for pn in PushNotification.objects.all():
        pn.regions.add(pn.region)


# pylint: disable=unused-argument
def reverse_func(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """
    Reverting (most of the) newer data when reverting this migration

    :param apps: The configuration of installed applications
    :param schema_editor: The database abstraction layer that creates actual SQL code
    """
    PushNotification = apps.get_model("cms", "PushNotification")
    for pn in PushNotification.objects.all():
        pn.region = pn.regions.first()
        pn.save()


class Migration(migrations.Migration):
    """
    Replace ReferenceField `region` with a ManyToManyField `regions` in PushNotification.
    """

    dependencies = [
        ("cms", "0074_pushnotification_scheduled_send_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="pushnotification",
            name="regions",
            field=models.ManyToManyField(
                related_name="push_notifications",
                to="cms.Region",
                verbose_name="regions",
            ),
        ),
        migrations.AlterField(
            model_name="pushnotification",
            name="region",
            field=models.ForeignKey(
                null=True,
                on_delete=CASCADE,
                related_name="push_notifications",
                to="cms.region",
                verbose_name="region",
            ),
        ),
        migrations.RunPython(forwards_func, reverse_func),
        migrations.RemoveField(
            model_name="pushnotification",
            name="region",
        ),
    ]
