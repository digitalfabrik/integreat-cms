from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Rename Contact.title to point_of_contact_for
    """

    dependencies = [
        ("cms", "0107_externalcalendar_author_fields"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="contact",
            name="contact_singular_empty_title_per_location",
        ),
        migrations.RemoveConstraint(
            model_name="contact",
            name="contact_non_empty",
        ),
        migrations.RenameField(
            model_name="contact",
            old_name="title",
            new_name="point_of_contact_for",
        ),
        migrations.AlterField(
            model_name="contact",
            name="point_of_contact_for",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="point of contact for",
            ),
        ),
        migrations.AddConstraint(
            model_name="contact",
            constraint=models.UniqueConstraint(
                models.F("location"),
                condition=models.Q(("point_of_contact_for", "")),
                name="contact_singular_empty_point_of_contact_per_location",
                violation_error_message="Only one contact per location can have an empty point of contact.",
            ),
        ),
        migrations.AddConstraint(
            model_name="contact",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("point_of_contact_for", ""), _negated=True),
                    models.Q(("name", ""), _negated=True),
                    models.Q(("email", ""), _negated=True),
                    models.Q(("phone_number", ""), _negated=True),
                    models.Q(("website", ""), _negated=True),
                    _connector="OR",
                ),
                name="contact_non_empty",
                violation_error_message="One of the following fields must be filled: point of contact for, name, e-mail, phone number, website.",
            ),
        ),
    ]
