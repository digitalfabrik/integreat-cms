# Generated by Django 3.2.20 on 2023-09-07 10:59

from __future__ import annotations

from typing import TYPE_CHECKING

from cacheops import invalidate_model
from django.db import migrations

from ..constants import region_status

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def update_mirrored_pages(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Set the field mirrored_page to None when a page is archived or belongs to an archived region.

    :param apps: The configuration of installed applications
    """

    Page = apps.get_model("cms", "Page")
    Region = apps.get_model("cms", "Region")

    pages_archived_region = Page.objects.filter(region__status=region_status.ARCHIVED)

    pages_archived = [
        Page.objects.filter(
            tree_id=page.tree_id,
            lft__range=(page.lft, page.rgt - 1),
        ).order_by()
        for page in Page.objects.filter(explicitly_archived=True)
    ]

    page_ids = pages_archived_region.union(*pages_archived).values_list("id", flat=True)

    Page.objects.filter(id__in=page_ids).update(mirrored_page=None)

    invalidate_model(Region)
    invalidate_model(Page)


class Migration(migrations.Migration):
    """
    Set the field mirrored page to None when a page is archived or belongs to an archived region.
    """

    dependencies = [
        ("cms", "0078_rename_usermfakey_userfidokey"),
    ]

    operations = [
        migrations.RunPython(update_mirrored_pages, migrations.RunPython.noop),
    ]
