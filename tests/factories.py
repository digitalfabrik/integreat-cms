"""
Factory functions for creating test objects.

These lightweight factories provide sensible defaults for all required fields
so tests only need to specify the values they care about. Prefer these over
raw ``objects.create()`` calls in new tests for consistency and readability.

Usage::

    from tests.factories import make_region, make_page, make_page_translation

    region = make_region()
    page = make_page(region)
    translation = make_page_translation(page, region.default_language, title="My Page")
"""

from __future__ import annotations

import datetime
from typing import Any
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model

from integreat_cms.cms.constants.administrative_division import MUNICIPALITY
from integreat_cms.cms.constants.region_status import ACTIVE
from integreat_cms.cms.constants.status import PUBLIC
from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Language,
    LanguageTreeNode,
    Page,
    PageTranslation,
    RecurrenceRule,
    Region,
)

User = get_user_model()

# Internal counter to generate unique slugs across a test run
_counter = 0


def _next_id() -> int:
    global _counter  # noqa: PLW0603
    _counter += 1
    return _counter


def make_language(slug: str | None = None, **overrides: Any) -> Language:
    """Create a :class:`~integreat_cms.cms.models.languages.language.Language`."""
    n = _next_id()
    defaults: dict[str, Any] = {
        "slug": slug or f"tl{n}",
        "bcp47_tag": f"tl-T{n}",
        "native_name": f"Test Language {n}",
        "english_name": f"Test Language {n}",
        "primary_country_code": "de",
        "table_of_contents": "Inhaltsverzeichnis",
    }
    defaults.update(overrides)
    return Language.objects.create(**defaults)


def make_region(slug: str | None = None, **overrides: Any) -> Region:
    """
    Create a :class:`~integreat_cms.cms.models.regions.region.Region`.

    If no language tree exists for the region after creation, a default
    language is created and attached automatically.
    """
    n = _next_id()
    defaults: dict[str, Any] = {
        "name": f"Test Region {n}",
        "slug": slug or f"test-region-{n}",
        "status": ACTIVE,
        "administrative_division": MUNICIPALITY,
        "postal_code": "00000",
        "admin_mail": f"admin{n}@example.com",
    }
    defaults.update(overrides)
    region = Region.objects.create(**defaults)
    # Ensure the region has at least one language so default_language works
    if not LanguageTreeNode.get_root_nodes().filter(region=region).exists():
        lang = make_language()
        LanguageTreeNode.add_root(language=lang, region=region)
    return region


def make_page(
    region: Region,
    parent: Page | None = None,
    **overrides: Any,
) -> Page:
    """
    Create a :class:`~integreat_cms.cms.models.pages.page.Page`.

    Uses treebeard's ``add_root`` / ``add_child`` API.
    """
    kwargs: dict[str, Any] = {"region": region}
    kwargs.update(overrides)
    if parent:
        return parent.add_child(**kwargs)
    return Page.add_root(**kwargs)


def make_page_translation(
    page: Page,
    language: Language | None = None,
    **overrides: Any,
) -> PageTranslation:
    """Create a :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation`."""
    n = _next_id()
    if language is None:
        language = page.region.default_language
    defaults: dict[str, Any] = {
        "page": page,
        "language": language,
        "title": f"Test Page {n}",
        "slug": f"test-page-{n}",
        "status": PUBLIC,
    }
    defaults.update(overrides)
    return PageTranslation.objects.create(**defaults)


def make_event(
    region: Region,
    start: datetime.datetime | None = None,
    end: datetime.datetime | None = None,
    **overrides: Any,
) -> Event:
    """Create a :class:`~integreat_cms.cms.models.events.event.Event`."""
    utc = ZoneInfo("UTC")
    if start is None:
        start = datetime.datetime(2030, 6, 1, 10, 0, tzinfo=utc)
    if end is None:
        end = start + datetime.timedelta(hours=1)
    defaults: dict[str, Any] = {
        "region": region,
        "start": start,
        "end": end,
    }
    defaults.update(overrides)
    return Event.objects.create(**defaults)


def make_event_translation(
    event: Event,
    language: Language | None = None,
    **overrides: Any,
) -> EventTranslation:
    """Create a :class:`~integreat_cms.cms.models.events.event_translation.EventTranslation`."""
    n = _next_id()
    if language is None:
        language = event.region.default_language
    defaults: dict[str, Any] = {
        "event": event,
        "language": language,
        "title": f"Test Event {n}",
        "slug": f"test-event-{n}",
    }
    defaults.update(overrides)
    return EventTranslation.objects.create(**defaults)


def make_recurrence_rule(**overrides: Any) -> RecurrenceRule:
    """Create a :class:`~integreat_cms.cms.models.events.recurrence_rule.RecurrenceRule`."""
    defaults: dict[str, Any] = {
        "frequency": "WEEKLY",
        "interval": 1,
    }
    defaults.update(overrides)
    return RecurrenceRule.objects.create(**defaults)


def make_user(username: str | None = None, **overrides: Any) -> Any:
    """Create a test user."""
    n = _next_id()
    defaults: dict[str, Any] = {
        "username": username or f"testuser{n}",
        "email": f"testuser{n}@example.com",
        "password": "test-password-1234!",
    }
    defaults.update(overrides)
    return User.objects.create_user(**defaults)
