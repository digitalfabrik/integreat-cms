from datetime import timedelta

import pytest
from django.utils import timezone

from integreat_cms.cms.constants import placecategory
from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Language,
    Place,
    PlaceCategory,
    PlaceTranslation,
    Region,
)


@pytest.mark.django_db
def test_event_restore_with_referenced_place() -> None:
    """
    Tests restoring an event restores its place together.
    """
    region = Region.objects.create(name="new-region")
    language = Language.objects.create(slug="da", primary_country_code="de")

    place_category = PlaceCategory.objects.create(
        icon=placecategory.OTHER,
        color=placecategory.DARK_BLUE,
    )
    place = Place.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
        archived=True,
    )
    PlaceTranslation.objects.create(
        place=place, language=language, slug="new-place-slug"
    )

    event = Event.objects.create(
        start=timezone.now(),
        end=timezone.now() + timedelta(days=1),
        region=region,
        archived=True,
        place=place,
    )
    EventTranslation.objects.create(
        event=event, language=language, slug="new-event-slug"
    )

    assert event.archived
    assert place.archived
    assert event.place.id == place.id

    event.restore()

    assert not event.archived
    assert not place.archived
