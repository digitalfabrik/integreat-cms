from __future__ import annotations

from typing import TYPE_CHECKING

import django.db.models.functions.text
from django.db import migrations, models

from integreat_cms.cms.utils.slug_utils import make_all_slug_lowercase

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def forwards(_apps: Apps, _schema_editor: BaseDatabaseSchemaEditor) -> None:
    make_all_slug_lowercase()


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
