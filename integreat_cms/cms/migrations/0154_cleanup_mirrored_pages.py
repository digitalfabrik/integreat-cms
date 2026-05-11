from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations
from django.db.models import Exists, OuterRef

from integreat_cms.cms.constants.status import PUBLIC

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def cleanup_mirrored_pages_with_no_public_translations(
    apps: Apps, _schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Page = apps.get_model("cms", "Page")
    PageTranslation = apps.get_model("cms", "PageTranslation")

    pages_to_update = (
        Page.objects.filter(mirrored_page__isnull=False)
        .annotate(
            has_public_translation=Exists(
                PageTranslation.objects.filter(
                    page=OuterRef("mirrored_page"),
                    status=PUBLIC,
                )
            )
        )
        .filter(has_public_translation=False)
    )
    pages_to_update.update(mirrored_page=None)


class Migration(migrations.Migration):
    """
    This migration sets the mirrored_page to null if the mirrored page has no public translations
    """

    dependencies = [
        ("cms", "0153_enforce_slug_uniqueness"),
    ]
    operations = [
        migrations.RunPython(
            cleanup_mirrored_pages_with_no_public_translations,
            migrations.RunPython.noop,
        ),
    ]
