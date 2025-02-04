from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations

from ..constants import status

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def update_poi_translation_status(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Update poi translation status to draft for pois without the default public translation

    :param apps: The configuration of installed applications
    """
    Region = apps.get_model("cms", "Region")
    POITranslation = apps.get_model("cms", "POITranslation")

    for region in Region.objects.filter(pois__isnull=False).distinct():
        default_language = region.language_tree_nodes.values_list(
            "language",
            flat=True,
        ).first()
        POITranslation.objects.filter(
            poi__region=region,
            status=status.PUBLIC,
        ).exclude(
            poi__in=region.pois.filter(
                translations__language=default_language,
                translations__status=status.PUBLIC,
            ),
        ).update(status=status.DRAFT)


class Migration(migrations.Migration):
    """
    Migration file to update poi translation status to draft for pois without the default public translation
    """

    dependencies = [
        ("cms", "0065_pagetranslation_hix_score"),
    ]

    operations = [
        migrations.RunPython(update_poi_translation_status, migrations.RunPython.noop),
    ]
