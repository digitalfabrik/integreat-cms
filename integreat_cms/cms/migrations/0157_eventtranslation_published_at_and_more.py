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
    Populate the new ``published_at`` field of existing content translations with the
    ``last_updated`` timestamp of the earliest public version of the same translation
    (i.e. per content object and language)

    :param apps: The configuration of installed applications
    """
    for translation_model_name, foreign_field in [
        ("EventTranslation", "event"),
        ("ImprintPageTranslation", "page"),
        ("PageTranslation", "page"),
        ("POITranslation", "poi"),
    ]:
        translation_model = apps.get_model("cms", translation_model_name)
        first_publication = (
            translation_model.objects.filter(
                **{foreign_field: OuterRef(foreign_field)},
                language=OuterRef("language"),
                status=status.PUBLIC,
            )
            .order_by("last_updated")
            .values("last_updated")[:1]
        )
        translation_model.objects.filter(published_at__isnull=True).update(
            published_at=Subquery(first_publication)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0156_remove_region_chat_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventtranslation",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="imprintpagetranslation",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="pagetranslation",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.AddField(
            model_name="poitranslation",
            name="published_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="publication date"
            ),
        ),
        migrations.RunPython(populate_published_at, migrations.RunPython.noop),
    ]
