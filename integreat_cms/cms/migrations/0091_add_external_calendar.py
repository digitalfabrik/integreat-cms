# Generated by Django 4.2.10 on 2024-05-19 14:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0090_pagetranslation_hix_feedback"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="external_event_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="The id of this event in the external calendar",
            ),
        ),
        migrations.CreateModel(
            name="ExternalCalendar",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        default="", max_length=255, verbose_name="calendar name"
                    ),
                ),
                ("url", models.CharField(max_length=255, verbose_name="URL")),
                (
                    "import_filter_tag",
                    models.CharField(
                        blank=True,
                        default="integreat",
                        max_length=255,
                        verbose_name="The tag that events need to have to get imported (Leave blank to import all events)",
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cms.region",
                        verbose_name="region",
                    ),
                ),
            ],
            options={
                "verbose_name": "external calendar",
                "verbose_name_plural": "external calendars",
                "default_permissions": ("change", "delete", "view"),
            },
        ),
        migrations.AddField(
            model_name="event",
            name="external_calendar",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to="cms.externalcalendar",
                verbose_name="external calendar",
            ),
        ),
    ]
