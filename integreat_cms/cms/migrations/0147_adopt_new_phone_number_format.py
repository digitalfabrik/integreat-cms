from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from django.db import migrations

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor

logger = logging.getLogger(__name__)


def migrate_phone_number_format(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Adopt existing phone numbers into the new format (remove "(0)")
    :param apps: The configuration of installed applications
    """

    Contact = apps.get_model("cms", "Contact")
    for contact in Contact.objects.all():
        phone_number = contact.phone_number
        if phone_number and "(0)" in phone_number:
            contact.phone_number = re.sub(r"\s*\(0\)\s*", " ", phone_number).strip()
        mobile_phone_number = contact.mobile_phone_number
        if mobile_phone_number and "(0)":
            contact.mobile_phone_number = re.sub(
                r"\s*\(0\)\s*", " ", mobile_phone_number
            ).strip()
        contact.save()


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0146_remove_pushnotification_draft_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_phone_number_format, migrations.RunPython.noop),
    ]
