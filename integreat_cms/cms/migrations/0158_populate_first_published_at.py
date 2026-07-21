from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations
from django.db.models import OuterRef, Subquery

from ..constants import status

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def populate_first_published_at(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Populate the new ``first_published_at`` field of existing content objects with the
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
        model.objects.update(first_published_at=Subquery(first_publication))


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0157_event_first_published_at_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_first_published_at, migrations.RunPython.noop),
    ]
