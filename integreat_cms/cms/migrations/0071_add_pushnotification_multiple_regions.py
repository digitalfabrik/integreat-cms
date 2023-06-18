from django.db import migrations, models
from django.db.models import OuterRef, Subquery, F


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0070_alter_poicategory_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='pushnotification',
            name='regions',
            field=models.ManyToManyField(related_name='push_notifications', to='cms.Region', verbose_name='regions'),
        ),
    ]
