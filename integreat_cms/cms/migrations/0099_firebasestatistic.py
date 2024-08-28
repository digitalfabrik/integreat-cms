from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Create FirebaseStatistic model
    """

    dependencies = [
        ("cms", "0098_add_contact"),
    ]

    operations = [
        migrations.CreateModel(
            name="FirebaseStatistic",
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
                ("date", models.DateField()),
                ("region", models.CharField(max_length=100)),
                ("language_slug", models.CharField(max_length=2)),
                ("count", models.IntegerField()),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
