"""
Test module for RecurrenceRule class
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from linkcheck.utils import find_all_links

from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Language,
    MediaFile,
    Organization,
    RecurrenceRule,
    Region,
)


class TestMediaFile:
    @pytest.mark.django_db
    def test_content_usage_count(self) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="example.pdf",
            thumbnail="example_thumbnail.jpg",
            file_size=1024,
            type="PDF",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        # Past event
        file.events.add(
            Event.objects.create(
                start=timezone.now() - timedelta(days=2),
                end=timezone.now() - timedelta(days=1),
                region=region,
            )
        )

        assert file.past_event_usages.count() == 1

    @pytest.mark.django_db
    def test_only_used_in_past_events(self) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="example.pdf",
            thumbnail="example_thumbnail.jpg",
            file_size=1024,
            type="PDF",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        # Past event
        file.events.add(
            Event.objects.create(
                start=timezone.now() - timedelta(days=2),
                end=timezone.now() - timedelta(days=1),
                region=region,
            )
        )

        assert file.is_only_used_in_past_events

    @pytest.mark.django_db
    def test_file_is_not_deletable_if_in_use(self) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="example.pdf",
            thumbnail="example_thumbnail.jpg",
            file_size=1024,
            type="PDF",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        # Past event
        file.events.add(
            Event.objects.create(
                start=timezone.now() - timedelta(days=2),
                end=timezone.now() - timedelta(days=1),
                region=region,
            )
        )

        # Upcoming event
        file.events.add(
            Event.objects.create(
                start=timezone.now() + timedelta(days=2),
                end=timezone.now() + timedelta(days=1),
                region=region,
            )
        )

        assert not file.is_deletable

    @pytest.mark.django_db
    def test_file_is_deletable_if_only_used_in_past_event(self) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="example.pdf",
            thumbnail="example_thumbnail.jpg",
            file_size=1024,
            type="PDF",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        # Past event
        file.events.add(
            Event.objects.create(
                start=timezone.now() - timedelta(days=2),
                end=timezone.now() - timedelta(days=1),
                region=region,
            )
        )

        assert file.is_deletable

    @pytest.mark.django_db
    def test_file_is_not_deletable_if_used_as_icon_and_by_past_event(self) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="example.pdf",
            thumbnail="example_thumbnail.jpg",
            file_size=1024,
            type="PDF",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        # Past event
        file.events.add(
            Event.objects.create(
                start=timezone.now() - timedelta(days=2),
                end=timezone.now() - timedelta(days=1),
                region=region,
            )
        )

        # Organization Icon
        Organization.objects.create(
            name="Beispiel-Organisation",
            slug="beispiel-organisation",
            website="https://example.com",
            region=region,
            icon=file,
        )

        assert not file.is_deletable

    @pytest.mark.django_db
    def test_is_not_deletable_if_used_as_organization_icon(self) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="example.pdf",
            thumbnail="example_thumbnail.jpg",
            file_size=1024,
            type="PDF",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        # Organization Icon
        Organization.objects.create(
            name="Beispiel-Organisation",
            slug="beispiel-organisation",
            website="https://example.com",
            region=region,
            icon=file,
        )

        assert not file.is_deletable

    @pytest.mark.django_db
    def test_is_not_deletable_if_used_as_within_translation_of_upcoming_event(
        self,
    ) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="bielefeld_stadtmarke.png",
            thumbnail="bielefeld_stadtmarke.png",
            file_size=1024,
            type="PNG",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        upcoming_event = Event.objects.create(
            start=timezone.now() + timedelta(days=1),
            end=timezone.now() + timedelta(days=2),
            region=region,
        )

        german_language = Language.objects.create(
            slug="de-test",
            bcp47_tag="de",
            native_name="Deutsch",
            english_name="German",
            text_direction="ltr",
            primary_country_code="DE",
            table_of_contents="Inhaltsverzeichnis",
        )

        EventTranslation.objects.create(
            event=upcoming_event,
            language=german_language,
            content=f'<p><img src="http://localhost:8000/media/{file.file}"></p>',
        )

        find_all_links()

        assert not file.is_deletable

    @pytest.mark.django_db
    def test_is_deletable_if_used_in_translation_of_past_event(self) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="bielefeld_stadtmarke.png",
            thumbnail="bielefeld_stadtmarke.png",
            file_size=1024,
            type="PNG",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        past_event = Event.objects.create(
            start=timezone.now() - timedelta(days=2),
            end=timezone.now() - timedelta(days=1),
            region=region,
        )

        german_language = Language.objects.create(
            slug="de-test",
            bcp47_tag="de",
            native_name="Deutsch",
            english_name="German",
            text_direction="ltr",
            primary_country_code="DE",
            table_of_contents="Inhaltsverzeichnis",
        )

        EventTranslation.objects.create(
            event=past_event,
            language=german_language,
            content=f'<p><img src="http://localhost:8000/media/{file.file}"></p>',
        )

        find_all_links()

        file.is_deletable

    @pytest.mark.django_db
    def test_is_deletable_when_used_in_translation_of_event_which_rrule_ended(
        self,
    ) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="bielefeld_stadtmarke.png",
            thumbnail="bielefeld_stadtmarke.png",
            file_size=1024,
            type="PNG",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        daily_rrule = RecurrenceRule.objects.create(
            interval=1,
            frequency="DAILY",
            weekdays_for_weekly=[0],
            recurrence_end_date=timezone.now() - timedelta(days=1),
        )

        past_event = Event.objects.create(
            start=timezone.now() - timedelta(days=10, hours=22),
            end=timezone.now() - timedelta(days=10, hours=23),
            region=region,
            recurrence_rule=daily_rrule,
        )

        german_language = Language.objects.create(
            slug="de-test",
            bcp47_tag="de",
            native_name="Deutsch",
            english_name="German",
            text_direction="ltr",
            primary_country_code="DE",
            table_of_contents="Inhaltsverzeichnis",
        )

        EventTranslation.objects.create(
            event=past_event,
            language=german_language,
            content=f'<p><img src="http://localhost:8000/media/{file.file}"></p>',
        )

        find_all_links()

        assert file.is_deletable

    @pytest.mark.django_db
    def test_is_not_deletable_when_used_in_translation_of_recurring_event(self) -> None:
        region = Region.objects.create(name="Testregion")

        file = MediaFile.objects.create(
            file="bielefeld_stadtmarke.png",
            thumbnail="bielefeld_stadtmarke.png",
            file_size=1024,
            type="PNG",
            name="Example File",
            alt_text="This is an example file",
            last_modified=datetime(2024, 4, 11, 10, 30, 0),
            is_hidden=False,
        )

        daily_rrule = RecurrenceRule.objects.create(
            interval=1,
            frequency="DAILY",
            weekdays_for_weekly=[0],
            recurrence_end_date=timezone.now() + timedelta(days=1),
        )

        recurring_event = Event.objects.create(
            start=timezone.now() - timedelta(days=10, hours=22),
            end=timezone.now() - timedelta(days=10, hours=23),
            region=region,
            recurrence_rule=daily_rrule,
        )

        german_language = Language.objects.create(
            slug="de-test",
            bcp47_tag="de",
            native_name="Deutsch",
            english_name="German",
            text_direction="ltr",
            primary_country_code="DE",
            table_of_contents="Inhaltsverzeichnis",
        )

        EventTranslation.objects.create(
            event=recurring_event,
            language=german_language,
            content=f'<p><img src="http://localhost:8000/media/{file.file}"></p>',
        )

        find_all_links()

        assert not file.is_deletable
