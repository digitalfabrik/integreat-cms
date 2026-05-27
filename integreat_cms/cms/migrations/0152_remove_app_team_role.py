from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def remove_app_team_role(apps: Apps, _schema_editor: BaseDatabaseSchemaEditor) -> None:
    # Use historical versions of the models
    User = apps.get_model("cms", "User")
    Group = apps.get_model("auth", "Group")
    Region = apps.get_model("cms", "Region")
    Role = apps.get_model("cms", "Role")

    app_team_group = Group.objects.filter(name="APP_TEAM").first()
    app_team_role = Role.objects.filter(name="APP_TEAM").first()

    if not app_team_group:
        return  # nothing to migrate users from

    management_group = Group.objects.filter(name="MANAGEMENT").first()
    if not management_group:
        raise RuntimeError(
            "MANAGEMENT group is missing, migration cannot proceed safely"
        )

    test_region = Region.objects.filter(slug="testumgebung").first()

    # Move users from APP_TEAM group to MANAGEMENT group and assign them to the Testumgebung region
    users = User._base_manager.filter(groups__id=app_team_group.id)
    users.update(is_staff=False, is_superuser=False)
    for user in users:
        user.groups.remove(app_team_group)
        user.groups.add(management_group)
        if test_region:
            user.regions.add(test_region)

    # Delete the old Role and Group objects
    app_team_group.delete()

    if app_team_role:
        app_team_role.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0151_alter_pushnotificationtranslation_title"),
    ]

    operations = [
        migrations.RunPython(remove_app_team_role, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="role",
            name="name",
            field=models.CharField(
                choices=[
                    ("MANAGEMENT", "Manager"),
                    ("EDITOR", "Editor"),
                    ("AUTHOR", "Author"),
                    ("EVENT_MANAGER", "Event manager"),
                    ("OBSERVER", "Observer"),
                    ("SERVICE_TEAM", "Service team"),
                    ("CMS_TEAM", "CMS team"),
                    ("MARKETING_TEAM", "Marketing team"),
                ],
                max_length=50,
                verbose_name="name",
            ),
        ),
    ]
