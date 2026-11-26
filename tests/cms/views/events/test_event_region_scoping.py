"""
Regression tests ensuring that the event form only resolves events and places of the
current region.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Event, EventTranslation

if TYPE_CHECKING:
    from django.test.client import Client

from tests.constants import ANONYMOUS

OWN_REGION_SLUG = "augsburg"
# Event 2 and place 5 belong to "nurnberg"
FOREIGN_EVENT_ID = 2
FOREIGN_PLACE_ID = 5

EVENT_DATA = {
    "content": "Lorem ipsum...",
    "start_date": "2030-01-01",
    "is_all_day": True,
    "is_long_term": False,
    "status": status.PUBLIC,
}


@pytest.mark.django_db
def test_edit_foreign_event_is_rejected(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    event = Event.objects.get(id=FOREIGN_EVENT_ID)
    region_before = event.region_id
    assert event.region.slug != OWN_REGION_SLUG

    url = reverse(
        "edit_event",
        kwargs={
            "region_slug": OWN_REGION_SLUG,
            "language_slug": "de",
            "event_id": FOREIGN_EVENT_ID,
        },
    )
    response = client.post(url, data={**EVENT_DATA, "title": "Hijacked event"})

    if role == ANONYMOUS:
        assert response.status_code == 302
    else:
        assert response.status_code in (403, 404)

    assert Event.objects.get(id=FOREIGN_EVENT_ID).region_id == region_before
    assert not EventTranslation.objects.filter(title="Hijacked event").exists()


@pytest.mark.django_db
def test_event_with_foreign_place_is_rejected(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    url = reverse(
        "new_event",
        kwargs={"region_slug": OWN_REGION_SLUG, "language_slug": "de"},
    )
    response = client.post(
        url,
        data={
            **EVENT_DATA,
            "title": "Event with foreign place",
            "place": FOREIGN_PLACE_ID,
        },
    )

    if role == ANONYMOUS:
        assert response.status_code == 302
    else:
        assert response.status_code in (200, 403)

    assert not EventTranslation.objects.filter(
        title="Event with foreign place"
    ).exists()
    assert not Event.objects.filter(
        region__slug=OWN_REGION_SLUG, place_id=FOREIGN_PLACE_ID
    ).exists()
