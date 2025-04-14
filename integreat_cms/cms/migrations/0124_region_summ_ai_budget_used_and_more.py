# Generated by Django 4.2.16 on 2025-04-14 15:03

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add fields for tracking SUMM.AI budget
    """

    dependencies = [
        ("cms", "0123_allow_svg_uploads"),
    ]

    operations = [
        migrations.AddField(
            model_name="region",
            name="summ_ai_budget_used",
            field=models.PositiveIntegerField(default=0, verbose_name="used budget"),
        ),
        migrations.AddField(
            model_name="region",
            name="summ_ai_midyear_start_month",
            field=models.PositiveIntegerField(
                blank=True,
                choices=[
                    (0, "January"),
                    (1, "February"),
                    (2, "March"),
                    (3, "April"),
                    (4, "May"),
                    (5, "June"),
                    (6, "July"),
                    (7, "August"),
                    (8, "September"),
                    (9, "October"),
                    (10, "November"),
                    (11, "December"),
                ],
                default=None,
                help_text="Month from which SUMM.AI was booked",
                null=True,
                verbose_name="Budget year start date for simplified language translation",
            ),
        ),
        migrations.AddField(
            model_name="region",
            name="summ_ai_renewal_month",
            field=models.PositiveIntegerField(
                choices=[
                    (0, "January"),
                    (1, "February"),
                    (2, "March"),
                    (3, "April"),
                    (4, "May"),
                    (5, "June"),
                    (6, "July"),
                    (7, "August"),
                    (8, "September"),
                    (9, "October"),
                    (10, "November"),
                    (11, "December"),
                ],
                default=0,
                help_text="Budget usage will be reset on the 1st of the month",
                verbose_name="Credits renewal date for simplified language translation",
            ),
        ),
    ]
