from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone
from freezegun import freeze_time

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Language,
    LanguageTreeNode,
    Region,
)


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


@pytest.mark.django_db
def test_published_at_is_set_per_language_on_first_publication() -> None:
    region = Region.objects.create(name="new-region")
    language = Language.objects.create(
        slug="da",
        bcp47_tag="da",
        primary_country_code="de",
    )
    other_language = Language.objects.create(
        slug="xy",
        bcp47_tag="xy",
        primary_country_code="de",
    )
    LanguageTreeNode.add_root(language=language, region=region)

    event = Event.objects.create(
        start=timezone.now(),
        end=timezone.now() + timedelta(days=1),
        region=region,
    )

    # Creating a draft translation does not set the publication date
    draft_translation = EventTranslation.objects.create(
        event=event,
        language=language,
        slug="new-event",
        status=status.DRAFT,
    )
    assert draft_translation.published_at is None

    # Publishing a translation sets its own publication date
    with freeze_time("2024-01-01 12:00:00"):
        public_translation = EventTranslation.objects.create(
            event=event,
            language=language,
            slug="new-event",
            status=status.PUBLIC,
            version=1,
        )
    published_at = public_translation.published_at
    assert published_at == public_translation.last_updated

    # A new version of the same translation keeps the original publication date
    with freeze_time("2024-01-02 12:00:00"):
        new_version = public_translation.create_new_version_copy()
        new_version.save()
    assert new_version.published_at == published_at
    assert new_version.last_updated != published_at

    # A translation in another language gets its own, independent publication date
    with freeze_time("2024-01-03 12:00:00"):
        other_translation = EventTranslation.objects.create(
            event=event,
            language=other_language,
            slug="new-event",
            status=status.PUBLIC,
        )
    assert other_translation.published_at == other_translation.last_updated
    assert other_translation.published_at != published_at
    # The first language keeps its original publication date
    public_translation.refresh_from_db()
    assert public_translation.published_at == published_at


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
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
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
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
