from django.db import migrations, models
from django.db.models import OuterRef, Subquery, F


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0072_datamigration_pushnotification_region_to_multiple_regions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pushnotification',
            name='region',
        ),
    ]
