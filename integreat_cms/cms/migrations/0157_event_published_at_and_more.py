from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations, models
from django.db.models import OuterRef, Subquery

from ..constants import status

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def populate_published_at(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Populate the new ``published_at`` field of existing content objects with the
    ``last_updated`` timestamp of their earliest public translation version

    :param apps: The configuration of installed applications
    """
    for model_name, translation_model_name, foreign_field in [
        ("Event", "EventTranslation", "event"),
        ("ImprintPage", "ImprintPageTranslation", "page"),
        ("Page", "PageTranslation", "page"),
        ("POI", "POITranslation", "poi"),
    ]:
        model = apps.get_model("cms", model_name)
        translation_model = apps.get_model("cms", translation_model_name)
        first_publication = (
            translation_model.objects.filter(
                **{foreign_field: OuterRef("pk")},
                status=status.PUBLIC,
            )
            .order_by("last_updated")
            .values("last_updated")[:1]
        )
        model.objects.filter(published_at__isnull=True).update(
            published_at=Subquery(first_publication)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0156_remove_region_chat_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="imprintpage",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="poi",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.RunPython(populate_published_at, migrations.RunPython.noop),
    ]
