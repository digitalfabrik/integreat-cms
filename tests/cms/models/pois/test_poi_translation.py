import pytest
from django.db import IntegrityError, transaction

from integreat_cms.cms.constants import poicategory
from integreat_cms.cms.models import Language, POI, POICategory, POITranslation, Region


@pytest.mark.django_db
def test_creating_poi_translations_to_automatically_create_unique_slugs() -> None:
    region = Region.objects.create(name="new-region")
    poi_category = POICategory.objects.create(
        icon=poicategory.OTHER,
        color=poicategory.DARK_BLUE,
    )
    poi1 = POI.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    poi2 = POI.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    poi3 = POI.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    language = Language.objects.create(slug="da", primary_country_code="de")
    poi_translation1 = POITranslation.objects.create(
        poi=poi1, language=language, slug="new-slug"
    )
    poi_translation2 = POITranslation.objects.create(
        poi=poi2, language=language, slug="new-slug"
    )
    poi_translation3 = POITranslation.objects.create(
        poi=poi3, language=language, slug="New-slug"
    )
    assert poi_translation1.slug != poi_translation2.slug != poi_translation3.slug


@pytest.mark.django_db
def test_creating_poi_translations_to_automatically_create_lowercase_slug() -> None:
    region = Region.objects.create(name="new-region")
    poi_category = POICategory.objects.create(
        icon=poicategory.OTHER,
        color=poicategory.DARK_BLUE,
    )
    poi1 = POI.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )

    language = Language.objects.create(slug="da", primary_country_code="de")
    poi_translation1 = POITranslation.objects.create(
        poi=poi1, language=language, slug="New-slug"
    )

    assert poi_translation1.slug == "new-slug"


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_db_trigger_prevents_duplicate_slug_on_poi_translations() -> None:
    region = Region.objects.create(slug="trigger-test-region")
    poi_category = POICategory.objects.create(
        icon=poicategory.OTHER,
        color=poicategory.DARK_BLUE,
    )
    poi1 = POI.objects.create(
        region=region,
        address="Test Street 1",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    poi2 = POI.objects.create(
        region=region,
        address="Test Street 2",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    language = Language.objects.create(slug="zz", primary_country_code="de")

    POITranslation.objects.create(poi=poi1, language=language, slug="conflict-slug")
    t2 = POITranslation.objects.create(poi=poi2, language=language, slug="other-slug")

    with pytest.raises(IntegrityError), transaction.atomic():
        # .update() bypasses save() and the application-level slug deduplication,
        # so only the database trigger prevents the duplicate
        POITranslation.objects.filter(pk=t2.pk).update(slug="conflict-slug")


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_db_trigger_enforce_slug_uniqueness_on_bulk_creation() -> None:
    region = Region.objects.create(slug="trigger-test-region")
    poi_category = POICategory.objects.create(
        icon=poicategory.OTHER,
        color=poicategory.DARK_BLUE,
    )
    poi1 = POI.objects.create(
        region=region,
        address="Test Street 1",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    poi2 = POI.objects.create(
        region=region,
        address="Test Street 2",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    language = Language.objects.create(slug="zz", primary_country_code="de")

    with pytest.raises(IntegrityError), transaction.atomic():
        # .update() bypasses save() and the application-level slug deduplication,
        # so only the database trigger prevents the duplicate
        POITranslation.objects.bulk_create(
            [
                POITranslation(poi=poi1, language=language, slug="conflict-slug"),
                POITranslation(poi=poi2, language=language, slug="conflict-slug"),
            ]
        )
