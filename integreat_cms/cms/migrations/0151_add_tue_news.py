import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0150_remove_user_page_tree_tutorial_seen_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="NewsLanguage",
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
                    "language",
                    models.CharField(
                        max_length=200,
                        verbose_name="Sprache",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        max_length=5,
                        verbose_name="Sprachcode",
                    ),
                ),
                (
                    "wpcategory",
                    models.IntegerField(
                        null=True,
                        unique=True,
                        verbose_name="WordPress-Kategorie-ID",
                    ),
                ),
            ],
            options={
                "verbose_name": "Sprache",
                "verbose_name_plural": "Sprachen",
            },
        ),
        migrations.CreateModel(
            name="NewsCategory",
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
                    models.CharField(max_length=200, verbose_name="Kategorie"),
                ),
            ],
            options={
                "verbose_name": "Nachrichtenkategorie",
                "verbose_name_plural": "Nachrichtenkategorien",
            },
        ),
        migrations.CreateModel(
            name="NewsItem",
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
                    "title",
                    models.CharField(
                        max_length=200,
                        verbose_name="Titel",
                    ),
                ),
                (
                    "content",
                    models.TextField(
                        verbose_name="Inhalt",
                    ),
                ),
                (
                    "enewsno",
                    models.CharField(
                        max_length=20,
                        verbose_name="E-News Nummer",
                    ),
                ),
                (
                    "pub_date",
                    models.DateTimeField(
                        verbose_name="Datum",
                    ),
                ),
                (
                    "newscategory",
                    models.ManyToManyField(
                        to="cms.NewsCategory",
                    ),
                ),
                (
                    "language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cms.newslanguage",
                    ),
                ),
                (
                    "wppostid",
                    models.IntegerField(
                        null=True,
                        unique=True,
                        verbose_name="WP Post ID",
                    ),
                ),
                (
                    "translations",
                    models.JSONField(
                        blank=True,
                        null=True,
                        verbose_name="Übersetzungen",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nachricht",
                "verbose_name_plural": "Nachrichten",
                "ordering": ["-enewsno"],
            },
        ),
    ]
