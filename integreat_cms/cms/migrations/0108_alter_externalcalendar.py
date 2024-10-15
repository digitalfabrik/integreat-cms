import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration file that adds the field created by to external calendars
    """

    dependencies = [
        ("cms", "0107_update_externalcalendar"),
    ]

    operations = [
        migrations.AddField(
            model_name="externalcalendar",
            name="last_changed_by",
            field=models.ForeignKey(
                blank=True,
                help_text="The account that was the last to change this external calendar.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="last_changed_by",
                to=settings.AUTH_USER_MODEL,
                verbose_name="last changed by",
            ),
        ),
        migrations.AddField(
            model_name="externalcalendar",
            name="last_changed_on",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="last changed on",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="externalcalendar",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                help_text="The account that created this external calendar.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_by",
                to=settings.AUTH_USER_MODEL,
                verbose_name="creator",
            ),
        ),
    ]
