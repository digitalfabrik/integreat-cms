# Generated by Django 4.2.10 on 2024-04-22 08:11

import django.db.models.deletion
from django.db import migrations, models

import integreat_cms.cms.models.chat.attachment_map


class Migration(migrations.Migration):
    """
    Add more Zammad configuration options for the chat API
    """

    dependencies = [
        ("cms", "0093_language_language_color"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserChat",
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
                ("device_id", models.CharField(max_length=200)),
                ("zammad_id", models.IntegerField()),
                ("most_recent_hits", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "user chat",
                "verbose_name_plural": "user chats",
                "ordering": ["-pk"],
                "default_permissions": ("delete", "change"),
            },
        ),
        migrations.AddField(
            model_name="region",
            name="zammad_access_token",
            field=models.CharField(
                blank=True,
                default="",
                help_text='Access token for a Zammad user account. In Zammad, the account must be part of the "Agent" role and have full group permissions for the group:',
                max_length=64,
                verbose_name="Zammad access token",
            ),
        ),
        migrations.AddField(
            model_name="region",
            name="zammad_chat_handlers",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Comma-separated email addresses of the accounts which should automatically be subscribed to new chat tickets. Note that these users must have full group permissions for the group:",
                max_length=1024,
                verbose_name="Zammad chat handlers",
            ),
        ),
        migrations.CreateModel(
            name="AttachmentMap",
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
                    "random_hash",
                    models.CharField(
                        default=integreat_cms.cms.models.chat.attachment_map.generate_random_hash,
                        max_length=64,
                        unique=True,
                    ),
                ),
                ("article_id", models.IntegerField()),
                ("attachment_id", models.IntegerField()),
                ("mime_type", models.CharField(max_length=32)),
                (
                    "user_chat",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="cms.userchat",
                    ),
                ),
            ],
            options={
                "verbose_name": "attachment map",
                "verbose_name_plural": "attachment maps",
                "ordering": ["-pk"],
                "default_permissions": ("delete", "change"),
            },
        ),
    ]