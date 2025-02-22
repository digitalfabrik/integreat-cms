# Generated by Django 4.2.13 on 2024-11-08 12:41

import uuid
from collections.abc import Callable

from django.apps.registry import Apps
from django.db import migrations, models


def set_zammad_urls(
    apps: Apps,
    _schema_editor: Callable,
) -> None:
    """
    Update empty Zammad URLs to Null
    """
    Region = apps.get_model("cms", "Region")
    Region.objects.filter(zammad_url=None).update(zammad_url="")
    for region in Region.objects.all():
        region.zammad_webhook_token = uuid.uuid4()
        region.save()


class Migration(migrations.Migration):
    """
    Remove zammad_url unique constraint, replace Null values with empty strings, remove null=true
    """

    dependencies = [
        ("cms", "0109_custom_truncating_char_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="region",
            name="zammad_webhook_token",
            field=models.UUIDField(
                blank=True,
                default=uuid.uuid4,
                help_text="Token used by Zammad webhooks to inform the Integreat CMS about changed tickets. The token has to be appended with a token= GET parameter to the webhook path.",
                verbose_name="Token used by Zammad webhook",
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="zammad_url",
            field=models.URLField(
                blank=True,
                default=None,
                help_text="URL pointing to this region's Zammad instance. Setting this enables Zammad form offers.",
                max_length=256,
                null=True,
                verbose_name="Zammad-URL",
            ),
        ),
        migrations.RunPython(set_zammad_urls),
        migrations.AlterField(
            model_name="region",
            name="zammad_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="URL pointing to this region's Zammad instance. Setting this enables Zammad form offers.",
                max_length=256,
                verbose_name="Zammad-URL",
            ),
        ),
    ]
