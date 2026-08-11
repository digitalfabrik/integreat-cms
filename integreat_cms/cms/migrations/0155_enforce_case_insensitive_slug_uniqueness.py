from __future__ import annotations

from typing import TYPE_CHECKING

import django.db.models.functions.text
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def forwards(apps: Apps, _schema_editor: BaseDatabaseSchemaEditor) -> None:
    """
    Lowercase all translation slugs and resolve the collisions this may create
    (e.g. ``Foo`` and ``foo`` both become ``foo``) by appending a counter, so
    the case-insensitive uniqueness constraints added below can be applied.

    This uses the historical models on purpose: relying on the runtime models
    would make an unrelated field that is added in a later migration part of the
    generated SQL, which would fail because its column does not exist yet.

    :param apps: The configuration of installed applications
    """
    for model_name, foreign_field, reserved_slugs in [
        ("EventTranslation", "event", ()),
        ("PageTranslation", "page", settings.RESERVED_REGION_PAGE_PATTERNS),
        ("POITranslation", "poi", ()),
    ]:
        translation_model = apps.get_model("cms", model_name)
        non_lowercase_translations = translation_model.objects.filter(
            ~Q(slug=Lower("slug")),
        ).select_related(foreign_field)
        for translation in non_lowercase_translations:
            foreign_object = getattr(translation, foreign_field)
            # Other translations in the same region and language that could collide
            other_translations = translation_model.objects.filter(
                language_id=translation.language_id,
                **{f"{foreign_field}__region_id": foreign_object.region_id},
            ).exclude(**{f"{foreign_field}_id": foreign_object.pk})
            base_slug = translation.slug.lower()
            unique_slug = base_slug
            counter = 1
            while (
                unique_slug in reserved_slugs
                or other_translations.filter(slug=unique_slug).exists()
            ):
                counter += 1
                unique_slug = f"{base_slug}-{counter}"
            translation.slug = unique_slug
            translation.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0154_remove_user_distribute_sidebar_boxes"),
    ]

    operations = [
        migrations.RunPython(
            forwards,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="eventtranslation",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("slug", django.db.models.functions.text.Lower("slug"))
                ),
                name="eventtranslation_slug_lowercase",
            ),
        ),
        migrations.AddConstraint(
            model_name="pagetranslation",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("slug", django.db.models.functions.text.Lower("slug"))
                ),
                name="pagetranslation_slug_lowercase",
            ),
        ),
        migrations.AddConstraint(
            model_name="poitranslation",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("slug", django.db.models.functions.text.Lower("slug"))
                ),
                name="poitranslation_slug_lowercase",
            ),
        ),
    ]
