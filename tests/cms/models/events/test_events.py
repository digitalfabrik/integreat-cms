from datetime import timedelta

import pytest
from django.utils import timezone

from integreat_cms.cms.constants import poicategory
from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Language,
    POI,
    POICategory,
    POITranslation,
    Region,
)


@pytest.mark.django_db
def test_event_restore_with_referenced_poi() -> None:
    """
    Tests restoring an event restores its location together.
    """
    region = Region.objects.create(name="new-region")
    language = Language.objects.create(slug="da", primary_country_code="de")

    poi_category = POICategory.objects.create(
        icon=poicategory.OTHER,
        color=poicategory.DARK_BLUE,
    )
    poi = POI.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
        archived=True,
    )
    POITranslation.objects.create(poi=poi, language=language, slug="new-poi-slug")

    event = Event.objects.create(
        start=timezone.now(),
        end=timezone.now() + timedelta(days=1),
        region=region,
        archived=True,
        location=poi,
    )
    EventTranslation.objects.create(
        event=event, language=language, slug="new-event-slug"
    )

    assert event.archived
    assert poi.archived
    assert event.location.id == poi.id

    event.restore()

    assert not event.archived
    assert not poi.archived
