from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def create_primary_contact(
    apps: Apps, _schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """
     Create primary contact for each POI and remove E-mail, phone number and website fields from POI model

    :param apps: The configuration of installed applications
    :param schema_editor: The database abstraction layer that creates actual SQL code
    """
    POI = apps.get_model("cms", "POI")
    Contact = apps.get_model("cms", "Contact")
    for poi in POI.objects.all():
        if (
            not Contact.objects.filter(location=poi, area_of_responsibility="").exists()
        ) and (poi.email or poi.phone_number or poi.website):
            primary_contact = Contact.objects.create(
                email=poi.email,
                phone_number=poi.phone_number,
                website=poi.website,
                area_of_responsibility="",
                name="",
                location=poi,
            )
            primary_contact.save()


class Migration(migrations.Migration):
    """
    Migrate contact data from poi to Contact model
    """

    dependencies = [
        ("cms", "0115_update_contact_permission"),
    ]

    operations = [
        migrations.RunPython(create_primary_contact),
        migrations.RemoveField(
            model_name="poi",
            name="email",
        ),
        migrations.RemoveField(
            model_name="poi",
            name="phone_number",
        ),
        migrations.RemoveField(
            model_name="poi",
            name="website",
        ),
    ]
