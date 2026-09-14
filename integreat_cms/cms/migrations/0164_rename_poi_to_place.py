import django.db.models.deletion
import django.db.models.functions.text
import pgtrigger.compiler
import pgtrigger.migrations
from django.apps.registry import Apps
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from integreat_cms.cms.constants import roles


def update_roles(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Assign the permissions of the renamed models to the roles

    :param apps: The configuration of installed applications
    """
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # Emit post-migrate signal to make sure the Permission objects are created before they can be assigned
    emit_post_migrate_signal(2, False, "default")

    Permission.objects.filter(
        codename__regex=r"^(change|delete|view)_poi(category(translation)?)?$",
    ).delete()

    # Clear and update permissions according to new constants
    for role_name in dict(roles.CHOICES):
        group, _ = Group.objects.get_or_create(name=role_name)
        # Clear permissions
        group.permissions.clear()
        # Set permissions
        group.permissions.add(
            *Permission.objects.filter(codename__in=roles.PERMISSIONS[role_name]),
        )


class Migration(migrations.Migration):
    """
    Rename the POI models and everything referring to them to "place"
    """

    dependencies = [
        ("cms", "0163_remove_user_expert_mode"),
    ]

    operations = [
        pgtrigger.migrations.RemoveTrigger(
            model_name="poitranslation",
            name="enforce_slug_uniqueness",
        ),
        migrations.RemoveConstraint(
            model_name="contact",
            name="contact_singular_empty_area_of_responsibility_per_location",
        ),
        migrations.RemoveConstraint(
            model_name="event",
            name="meeting_url_requires_no_location",
        ),
        migrations.RemoveConstraint(
            model_name="poitranslation",
            name="poitranslation_unique_version",
        ),
        migrations.RemoveConstraint(
            model_name="poitranslation",
            name="poitranslation_slug_lowercase",
        ),
        migrations.RenameModel(old_name="POI", new_name="Place"),
        migrations.RenameModel(old_name="POITranslation", new_name="PlaceTranslation"),
        migrations.RenameModel(old_name="POICategory", new_name="PlaceCategory"),
        migrations.RenameModel(
            old_name="POICategoryTranslation",
            new_name="PlaceCategoryTranslation",
        ),
        migrations.RenameModel(old_name="POIFeedback", new_name="PlaceFeedback"),
        migrations.RenameField(
            model_name="place",
            old_name="location_on_map",
            new_name="place_on_map",
        ),
        migrations.RenameField(
            model_name="placetranslation",
            old_name="poi",
            new_name="place",
        ),
        migrations.RenameField(
            model_name="placefeedback",
            old_name="poi_translation",
            new_name="place_translation",
        ),
        migrations.RenameField(
            model_name="contact",
            old_name="location",
            new_name="place",
        ),
        migrations.RenameField(
            model_name="event",
            old_name="location",
            new_name="place",
        ),
        migrations.RenameField(
            model_name="region",
            old_name="machine_translate_pois",
            new_name="machine_translate_places",
        ),
        migrations.AlterModelOptions(
            name="contact",
            options={
                "default_permissions": ("change", "delete", "view", "archive"),
                "default_related_name": "contact",
                "ordering": ["place", "name"],
                "verbose_name": "contact",
                "verbose_name_plural": "contacts",
            },
        ),
        migrations.AlterModelOptions(
            name="place",
            options={
                "default_permissions": ("change", "delete", "view"),
                "default_related_name": "places",
                "ordering": ["pk"],
                "verbose_name": "place",
                "verbose_name_plural": "places",
            },
        ),
        migrations.AlterModelOptions(
            name="placecategory",
            options={
                "default_permissions": ("change", "delete", "view"),
                "verbose_name": "place category",
                "verbose_name_plural": "place categories",
            },
        ),
        migrations.AlterModelOptions(
            name="placecategorytranslation",
            options={
                "default_permissions": ("change", "delete", "view"),
                "ordering": ["category"],
                "verbose_name": "place category translation",
                "verbose_name_plural": "place category translations",
            },
        ),
        migrations.AlterModelOptions(
            name="placefeedback",
            options={
                "default_permissions": (),
                "verbose_name": "place feedback",
                "verbose_name_plural": "place feedback",
            },
        ),
        migrations.AlterModelOptions(
            name="placetranslation",
            options={
                "default_permissions": (),
                "default_related_name": "place_translations",
                "ordering": ["place__pk", "language__pk", "-version"],
                "verbose_name": "place translation",
                "verbose_name_plural": "place translations",
            },
        ),
        migrations.AlterField(
            model_name="contact",
            name="archived",
            field=models.BooleanField(
                default=False,
                help_text="Whether or not the place is read-only and hidden in the API.",
                verbose_name="archived",
            ),
        ),
        migrations.AlterField(
            model_name="contact",
            name="place",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="contacts",
                to="cms.place",
                verbose_name="place",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="meeting_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Link to the online event if it has no physical place.",
                verbose_name="Online event link",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="place",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="cms.place",
                verbose_name="place",
            ),
        ),
        migrations.AlterField(
            model_name="place",
            name="appointment_url",
            field=models.URLField(
                blank=True,
                help_text="Link to an external website where an appointment for this place can be made.",
                max_length=500,
                verbose_name="appointment link",
            ),
        ),
        migrations.AlterField(
            model_name="place",
            name="archived",
            field=models.BooleanField(
                default=False,
                help_text="Whether or not the place is read-only and hidden in the API.",
                verbose_name="archived",
            ),
        ),
        migrations.AlterField(
            model_name="place",
            name="barrier_free",
            field=models.BooleanField(
                default=None,
                help_text="Indicate if the place is barrier free.",
                null=True,
                verbose_name="barrier free",
            ),
        ),
        migrations.AlterField(
            model_name="place",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="places",
                to="cms.placecategory",
                verbose_name="category",
            ),
        ),
        migrations.AlterField(
            model_name="place",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                help_text="Specify which organization operates this place.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="places",
                to="cms.organization",
                verbose_name="organization",
            ),
        ),
        migrations.AlterField(
            model_name="place",
            name="place_on_map",
            field=models.BooleanField(
                default=False,
                help_text="Tick if you want to show this place on map",
                verbose_name="Show this place on map",
            ),
        ),
        migrations.AlterField(
            model_name="place",
            name="temporarily_closed",
            field=models.BooleanField(
                default=False,
                help_text="Whether or not the place is temporarily closed. The opening hours remain and are only hidden.",
                verbose_name="temporarily closed",
            ),
        ),
        migrations.AlterField(
            model_name="placecategorytranslation",
            name="language",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="place_category_translations",
                to="cms.language",
                verbose_name="language",
            ),
        ),
        migrations.AlterField(
            model_name="placecategorytranslation",
            name="name",
            field=models.CharField(
                help_text="The name of the place category.",
                max_length=250,
                verbose_name="category name",
            ),
        ),
        migrations.AlterField(
            model_name="placefeedback",
            name="place_translation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="feedback",
                to="cms.placetranslation",
                verbose_name="place translation",
            ),
        ),
        migrations.AlterField(
            model_name="placetranslation",
            name="meta_description",
            field=models.CharField(
                blank=True,
                help_text="Describe the place in one or two short sentences. This text will be displayed in the Google search results below the title.",
                max_length=2048,
                verbose_name="meta description",
            ),
        ),
        migrations.AlterField(
            model_name="placetranslation",
            name="place",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="translations",
                to="cms.place",
                verbose_name="place",
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="fallback_translations_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Whether or not events and places are shown in default language as fallback",
                verbose_name="Show content in default language as fallback",
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="locations_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Whether or not places are enabled in the region",
                verbose_name="activate places",
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="machine_translate_places",
            field=models.PositiveIntegerField(
                choices=[(0, "No"), (1, "Yes"), (2, "Yes, only managers")],
                default=1,
                verbose_name="Places",
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="seo_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Enable possibility to fill meta description for pages, events and places",
                verbose_name="activate SEO section",
            ),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="placetranslation",
            trigger=pgtrigger.compiler.Trigger(
                name="enforce_slug_uniqueness",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    func="\n                DECLARE\n                    new_region_id INTEGER;\n                BEGIN\n                    -- Look up the region for the new/updated place\n                    SELECT region_id INTO new_region_id\n                    FROM cms_place\n                    WHERE id = NEW.place_id;\n\n                    -- Set advisory lock (Postgresql specific)\n                    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.language_id || ':' || new_region_id || ':' || NEW.slug, 0));\n\n                    -- Check if there's a conflict (same slug/language/region but different place)\n                    IF EXISTS (\n                        SELECT 1\n                        FROM cms_placetranslation t\n                        JOIN cms_place p ON t.place_id = p.id\n                        WHERE t.slug = NEW.slug\n                        AND t.language_id = NEW.language_id\n                        AND p.region_id = new_region_id\n                        AND t.place_id <> NEW.place_id\n                    ) THEN\n                        RAISE EXCEPTION 'Slug must be unique per language and region across different places.' USING ERRCODE = 'unique_violation'; -- SQLSTATE 23505\n                    END IF;\n\n                    RETURN NEW;\n                END;\n                ",
                    hash="e1810000dc54de7ae64a631807585b4aa27d3688",
                    operation="INSERT OR UPDATE",
                    pgid="pgtrigger_enforce_slug_uniqueness_ab870",
                    table="cms_placetranslation",
                    when="BEFORE",
                ),
            ),
        ),
        migrations.AddConstraint(
            model_name="contact",
            constraint=models.UniqueConstraint(
                models.F("place"),
                condition=models.Q(("area_of_responsibility", "")),
                name="contact_singular_empty_area_of_responsibility_per_place",
                violation_error_message="Only one contact per place can have an empty area of responsibility.",
            ),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("meeting_url", ""), ("place", None), _connector="OR"
                ),
                name="meeting_url_requires_no_place",
                violation_error_message="An event with a place can't have a meeting URL",
            ),
        ),
        migrations.AddConstraint(
            model_name="placetranslation",
            constraint=models.UniqueConstraint(
                fields=("place", "language", "version"),
                name="placetranslation_unique_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="placetranslation",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("slug", django.db.models.functions.text.Lower("slug"))
                ),
                name="placetranslation_slug_lowercase",
            ),
        ),
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ]
