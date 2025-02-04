from django.db import migrations

import integreat_cms.cms.models.fields.truncating_char_field


class Migration(migrations.Migration):
    """
    Migration file to change the field point_of_contact_for from a CharField to a TruncatingCharField
    """

    dependencies = [
        ("cms", "0108_rename_contact_title_to_point_of_contact_for"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="point_of_contact_for",
            field=integreat_cms.cms.models.fields.truncating_char_field.TruncatingCharField(
                blank=True,
                max_length=200,
                verbose_name="point of contact for",
            ),
        ),
        migrations.AlterField(
            model_name="eventtranslation",
            name="title",
            field=integreat_cms.cms.models.fields.truncating_char_field.TruncatingCharField(
                max_length=1024,
                verbose_name="title",
            ),
        ),
        migrations.AlterField(
            model_name="imprintpagetranslation",
            name="title",
            field=integreat_cms.cms.models.fields.truncating_char_field.TruncatingCharField(
                max_length=1024,
                verbose_name="title",
            ),
        ),
        migrations.AlterField(
            model_name="pagetranslation",
            name="title",
            field=integreat_cms.cms.models.fields.truncating_char_field.TruncatingCharField(
                max_length=1024,
                verbose_name="title",
            ),
        ),
        migrations.AlterField(
            model_name="poitranslation",
            name="title",
            field=integreat_cms.cms.models.fields.truncating_char_field.TruncatingCharField(
                max_length=1024,
                verbose_name="title",
            ),
        ),
    ]
