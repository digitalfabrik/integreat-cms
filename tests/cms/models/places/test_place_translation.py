import pytest
from django.db import IntegrityError, transaction

from integreat_cms.cms.constants import placecategory
from integreat_cms.cms.models import (
    Language,
    Place,
    PlaceCategory,
    PlaceTranslation,
    Region,
)


@pytest.mark.django_db
def test_creating_place_translations_to_automatically_create_unique_slugs() -> None:
    region = Region.objects.create(name="new-region")
    place_category = PlaceCategory.objects.create(
        icon=placecategory.OTHER,
        color=placecategory.DARK_BLUE,
    )
    place1 = Place.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )
    place2 = Place.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )
    place3 = Place.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )
    language = Language.objects.create(slug="da", primary_country_code="de")
    place_translation1 = PlaceTranslation.objects.create(
        place=place1, language=language, slug="new-slug"
    )
    place_translation2 = PlaceTranslation.objects.create(
        place=place2, language=language, slug="new-slug"
    )
    place_translation3 = PlaceTranslation.objects.create(
        place=place3, language=language, slug="New-slug"
    )
    assert place_translation1.slug != place_translation2.slug != place_translation3.slug


@pytest.mark.django_db
def test_creating_place_translations_to_automatically_create_lowercase_slug() -> None:
    region = Region.objects.create(name="new-region")
    place_category = PlaceCategory.objects.create(
        icon=placecategory.OTHER,
        color=placecategory.DARK_BLUE,
    )
    place1 = Place.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )

    language = Language.objects.create(slug="da", primary_country_code="de")
    place_translation1 = PlaceTranslation.objects.create(
        place=place1, language=language, slug="New-slug"
    )

    assert place_translation1.slug == "new-slug"


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True)
def test_db_trigger_prevents_duplicate_slug_on_place_translations() -> None:
    region = Region.objects.create(slug="trigger-test-region")
    place_category = PlaceCategory.objects.create(
        icon=placecategory.OTHER,
        color=placecategory.DARK_BLUE,
    )
    place1 = Place.objects.create(
        region=region,
        address="Test Street 1",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )
    place2 = Place.objects.create(
        region=region,
        address="Test Street 2",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )
    language = Language.objects.create(slug="zz", primary_country_code="de")

    PlaceTranslation.objects.create(
        place=place1, language=language, slug="conflict-slug"
    )
    t2 = PlaceTranslation.objects.create(
        place=place2, language=language, slug="other-slug"
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        # .update() bypasses save() and the application-level slug deduplication,
        # so only the database trigger prevents the duplicate
        PlaceTranslation.objects.filter(pk=t2.pk).update(slug="conflict-slug")


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True)
def test_db_trigger_enforce_slug_uniqueness_on_bulk_creation() -> None:
    region = Region.objects.create(slug="trigger-test-region")
    place_category = PlaceCategory.objects.create(
        icon=placecategory.OTHER,
        color=placecategory.DARK_BLUE,
    )
    place1 = Place.objects.create(
        region=region,
        address="Test Street 1",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )
    place2 = Place.objects.create(
        region=region,
        address="Test Street 2",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )
    language = Language.objects.create(slug="zz", primary_country_code="de")

    with pytest.raises(IntegrityError), transaction.atomic():
        # .update() bypasses save() and the application-level slug deduplication,
        # so only the database trigger prevents the duplicate
        PlaceTranslation.objects.bulk_create(
            [
                PlaceTranslation(place=place1, language=language, slug="conflict-slug"),
                PlaceTranslation(place=place2, language=language, slug="conflict-slug"),
            ]
        )
