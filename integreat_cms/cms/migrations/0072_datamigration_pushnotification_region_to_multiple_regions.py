from django.db import migrations, models
from django.db.models import OuterRef, Subquery, F


def forwards_func(apps, schema_editor):
    # Adopting the old data when applying this migration
    PushNotification = apps.get_model("cms", "PushNotification")
    db_alias = schema_editor.connection.alias
    """
    q = PushNotification.objects.using(db_alias).update(regions=F('region'))
    print('\n')
    print(q.explain())
    print()
    """
    for pn in PushNotification.objects.using(db_alias).all():
        pn.regions.add(pn.region)


def reverse_func(apps, schema_editor):
    # Reverting (most of the) newer data when reverting this migration
    PushNotification = apps.get_model("cms", "PushNotification")
    db_alias = schema_editor.connection.alias
    pns = PushNotification.objects.using(db_alias)
    first_regions = pns.filter(pk=OuterRef('pk')).values('regions').first()
    pns.update(region=Subquery(first_regions))


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0071_add_pushnotification_multiple_regions'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
