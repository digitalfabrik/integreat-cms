# Generated by Django 4.2.13 on 2024-09-23 15:33

from collections.abc import Callable

import django.db.models.deletion
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
    Region.objects.filter(zammad_url="").update(zammad_url=None)


class Migration(migrations.Migration):
    """
    Add relation between user chats and regions/languages.
    """

    dependencies = [("cms", "0103_alter_language_primary_country_code_and_more")]

    operations = [
        migrations.AddField(
            model_name="userchat",
            name="language",
            field=models.ForeignKey(
                default=3,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chats",
                to="cms.language",
                verbose_name="Language of chat app user",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="userchat",
            name="region",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chats",
                to="cms.region",
                verbose_name="Region for Chat",
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="zammad_url",
            field=models.URLField(
                blank=True,
                default="",
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
                default=None,
                help_text="URL pointing to this region's Zammad instance. Setting this enables Zammad form offers.",
                max_length=256,
                null=True,
                unique=True,
                verbose_name="Zammad-URL",
            ),
        ),
    ]
