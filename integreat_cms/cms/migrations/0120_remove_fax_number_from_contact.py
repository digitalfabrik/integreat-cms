# Generated by Django 4.2.16 on 2025-03-10 15:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0119_add_mobile_number_and_fax_number_to_contact"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="contact",
            name="contact_non_empty",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="fax_number",
        ),
        migrations.AddConstraint(
            model_name="contact",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("area_of_responsibility", ""), _negated=True),
                    models.Q(("name", ""), _negated=True),
                    models.Q(("email", ""), _negated=True),
                    models.Q(("phone_number", ""), _negated=True),
                    models.Q(("mobile_phone_number", ""), _negated=True),
                    models.Q(("website", ""), _negated=True),
                    _connector="OR",
                ),
                name="contact_non_empty",
                violation_error_message="One of the following fields must be filled: area of responsibility, name, e-mail, phone number, mobile phone number, website.",
            ),
        ),
    ]
