from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.constants import ANONYMOUS, REGION_ROLES, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"
LANGUAGE_SLUG = "de"

# Events in Augsburg test data have title "Test-Veranstaltung"

AUTHORIZED_ROLES = [*STAFF_ROLES, *REGION_ROLES]


@pytest.mark.django_db
def test_event_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the event list filters by title and only shows matching events.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse(
        "events",
        kwargs={"region_slug": REGION_SLUG, "language_slug": LANGUAGE_SLUG},
    )
    # Search for existing event title
    response = client.get(url, {"search_query": "Test-Veranstaltung"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in AUTHORIZED_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Test-Veranstaltung" in content


@pytest.mark.django_db
def test_event_list_search_nonexistent_returns_empty(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching for a non-existent event returns no results.
    """
    client, role = login_role_user

    url = reverse(
        "events",
        kwargs={"region_slug": REGION_SLUG, "language_slug": LANGUAGE_SLUG},
    )
    response = client.get(url, {"search_query": "ZZZNonExistentEvent"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in AUTHORIZED_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Test-Veranstaltung" not in content
