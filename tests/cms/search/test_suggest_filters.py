"""
Regression tests for search-suggestion filtering.

These cover four filters that the list-view search box enforced before the
``search_suggest`` refactor and which ``suggest_tokens`` must keep honoring:

* item 1 — suggestions are scoped to the current language
* item 2 — Feedback suggestions respect the ``is_technical`` admin/region split
* item 3 — archived list views suggest archived records only (and vice-versa)
* item 4 — unpublished (draft) translation titles are not suggested
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Feedback,
    Language,
    Region,
)

REGION_SLUG = "augsburg"


def _suggestions(result: dict) -> list[str]:
    return [entry["suggestion"] for entry in result["suggestions"]]


@pytest.mark.django_db
def test_event_suggestions_are_language_scoped(load_test_data: None) -> None:
    """
    Item 1: Event 1 (Augsburg) has the German title "Test-Veranstaltung mit
    neuem Titel" and the English title "Test-Event". The English title must not
    appear among the German list's suggestions.
    """
    region = Region.objects.get(slug=REGION_SLUG)

    english = _suggestions(
        EventTranslation.suggest_tokens(
            query="Test-Event", region=region, language_slug="en"
        )
    )
    german = _suggestions(
        EventTranslation.suggest_tokens(
            query="Test-Event", region=region, language_slug="de"
        )
    )

    assert "Test-Event" in english, "English list should suggest the English title"
    assert "Test-Event" not in german, "German list must not leak the English title"


@pytest.mark.django_db
def test_feedback_suggestions_respect_is_technical(load_test_data: None) -> None:
    """
    Item 2: the admin feedback list (region=None) shows only technical feedback,
    while a regional feedback list shows only that region's (non-technical)
    feedback. Suggestions must mirror that split.
    """
    region = Region.objects.get(slug=REGION_SLUG)

    admin = _suggestions(Feedback.suggest_tokens(query="feedback", region=None))
    regional = _suggestions(Feedback.suggest_tokens(query="feedback", region=region))

    # Admin (technical) feedback list
    assert "Feedback unread and not archived" in admin
    assert "Region feedback unread and not archived" not in admin

    # Regional (non-technical) feedback list
    assert "Region feedback unread and not archived" in regional
    assert "Feedback unread and not archived" not in regional


@pytest.mark.django_db
def test_archived_list_suggests_only_archived_records(load_test_data: None) -> None:
    """
    Item 3: the active list suggests only active records and the archived list
    suggests only archived records. Demonstrated with one active and one
    archived event sharing the query prefix "zqevt".
    """
    region = Region.objects.get(slug=REGION_SLUG)
    german = Language.objects.get(slug="de")
    now = timezone.now()

    active_event = Event.objects.create(
        start=now, end=now + timedelta(days=1), region=region
    )
    archived_event = Event.objects.create(
        start=now, end=now + timedelta(days=1), region=region, archived=True
    )
    EventTranslation.objects.create(
        event=active_event,
        language=german,
        title="Zqevtactive",
        slug="zqevtactive",
        status=status.PUBLIC,
        version=1,
    )
    EventTranslation.objects.create(
        event=archived_event,
        language=german,
        title="Zqevtarchived",
        slug="zqevtarchived",
        status=status.PUBLIC,
        version=1,
    )

    active = _suggestions(
        EventTranslation.suggest_tokens(
            query="zqevt", region=region, language_slug="de", archived=False
        )
    )
    archived = _suggestions(
        EventTranslation.suggest_tokens(
            query="zqevt", region=region, language_slug="de", archived=True
        )
    )

    assert "Zqevtactive" in active
    assert "Zqevtarchived" not in active

    assert "Zqevtarchived" in archived
    assert "Zqevtactive" not in archived


@pytest.mark.django_db
def test_draft_translations_are_not_suggested(load_test_data: None) -> None:
    """
    Item 4: the newest revision of Event 1's German translation is an
    unpublished draft with a distinctive title. Search must keep suggesting the
    latest *published* title and never the draft's title.
    """
    region = Region.objects.get(slug=REGION_SLUG)
    event = Event.objects.get(pk=1)
    german = Language.objects.get(slug="de")
    EventTranslation.objects.create(
        event=event,
        language=german,
        title="Zqdraftonlytitle",
        slug="zqdraftonlytitle",
        status=status.DRAFT,
        version=99,
    )

    drafted = _suggestions(
        EventTranslation.suggest_tokens(
            query="Zqdraftonlytitle", region=region, language_slug="de"
        )
    )
    assert "Zqdraftonlytitle" not in drafted

    published = _suggestions(
        EventTranslation.suggest_tokens(
            query="Test-Veranstaltung", region=region, language_slug="de"
        )
    )
    assert "Test-Veranstaltung mit neuem Titel" in published
