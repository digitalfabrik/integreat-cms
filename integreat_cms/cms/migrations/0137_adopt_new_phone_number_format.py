from __future__ import annotations

import logging
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
        if phone_number and phone_number.startswith("+49 (0) "):
            contact.phone_number = f"+49{phone_number[8:]}"
        mobile_phone_number = contact.mobile_phone_number
        if mobile_phone_number and mobile_phone_number.startswith("+49 (0) "):
            contact.mobile_phone_number = f"+49{mobile_phone_number[8:]}"
        contact.save()


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0136_event_online_link"),
    ]

    operations = [
        migrations.RunPython(migrate_phone_number_format, migrations.RunPython.noop),
    ]
