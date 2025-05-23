# Generated by Django 3.2.22 on 2023-11-02 09:40

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add and change fields required for Zammad forms as offers
    """

    dependencies = [
        ("cms", "0083_add_page_based_offer_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="offertemplate",
            name="is_zammad_form",
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text="Whether this offer should be treated as a Zammad form by the App",
                verbose_name="is Zammad form",
            ),
        ),
        migrations.AddField(
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
        migrations.AlterField(
            model_name="offertemplate",
            name="thumbnail",
            field=models.URLField(
                blank=True,
                max_length=250,
                verbose_name="thumbnail URL",
            ),
        ),
        migrations.AlterField(
            model_name="offertemplate",
            name="url",
            field=models.URLField(
                blank=True,
                help_text="This will be an external API endpoint in most cases.",
                max_length=250,
                verbose_name="URL",
            ),
        ),
    ]
