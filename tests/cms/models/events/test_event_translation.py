from datetime import timedelta

import pytest
from django.utils import timezone

from integreat_cms.cms.models import Event, EventTranslation, Language, Region


@pytest.mark.django_db
def test_when_creating_even_translations_to_automatically_create_unique_slugs() -> None:
    region = Region.objects.create(name="new-region")

    event1 = Event.objects.create(
        start=timezone.now(),
        end=timezone.now() + timedelta(days=1),
        region=region,
    )
    event2 = Event.objects.create(
        start=timezone.now(),
        end=timezone.now() + timedelta(days=2),
        region=region,
    )
    language = Language.objects.create(slug="da", primary_country_code="de")

    event_translation1 = EventTranslation.objects.create(
        event=event1, language=language, slug="new-slug"
    )
    event_translation2 = EventTranslation.objects.create(
        event=event2, language=language, slug="new-slug"
    )

    assert event_translation1.slug != event_translation2.slug
