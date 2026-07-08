from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
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
    event3 = Event.objects.create(
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
    event_translation3 = EventTranslation.objects.create(
        event=event3, language=language, slug="New-slug"
    )

    assert event_translation1.slug != event_translation2.slug != event_translation3.slug


@pytest.mark.django_db
def test_when_creating_even_translations_to_automatically_create_lowercase_slug() -> (
    None
):
    region = Region.objects.create(name="new-region")

    event1 = Event.objects.create(
        start=timezone.now(),
        end=timezone.now() + timedelta(days=1),
        region=region,
    )
    language = Language.objects.create(slug="da", primary_country_code="de")

    event_translation1 = EventTranslation.objects.create(
        event=event1, language=language, slug="New-slug"
    )

    assert event_translation1.slug == "new-slug"


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True)
def test_db_trigger_enforce_slug_uniqueness_on_event_translations() -> None:
    region = Region.objects.create(slug="trigger-test-region")
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
    language = Language.objects.create(slug="zz", primary_country_code="de")

    EventTranslation.objects.create(
        event=event1, language=language, slug="conflict-slug"
    )
    t2 = EventTranslation.objects.create(
        event=event2, language=language, slug="other-slug"
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        # .update() bypasses save() and the application-level slug deduplication,
        # so only the database trigger prevents the duplicate
        EventTranslation.objects.filter(pk=t2.pk).update(slug="conflict-slug")


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True)
def test_db_trigger_enforce_slug_uniqueness_on_bulk_creation() -> None:
    region = Region.objects.create(slug="trigger-test-region")
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
    language = Language.objects.create(slug="zz", primary_country_code="de")

    with pytest.raises(IntegrityError), transaction.atomic():
        # .bulk_create() bypasses save() and the application-level slug deduplication,
        # so only the database trigger prevents the duplicate
        EventTranslation.objects.bulk_create(
            [
                EventTranslation(event=event1, language=language, slug="conflict-slug"),
                EventTranslation(event=event2, language=language, slug="conflict-slug"),
            ]
        )
