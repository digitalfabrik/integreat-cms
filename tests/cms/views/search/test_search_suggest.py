"""
Tests for the search_suggest view
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from integreat_cms.cms.constants.roles import CMS_TEAM, EVENT_MANAGER, OBSERVER
from tests.conftest import ANONYMOUS

# Roles that have view_page permission (all except EVENT_MANAGER)
# Roles that have view_contact permission (all except EVENT_MANAGER and OBSERVER)

if TYPE_CHECKING:
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

# Use the region Augsburg, as it has test data
REGION_SLUG = "augsburg"
LANGUAGE_SLUG = "de"


@pytest.mark.django_db
def test_search_suggest_returns_suggestions(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that search_suggest returns suggestions for valid queries
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    url = reverse(
        "search_suggest",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": LANGUAGE_SLUG,
        },
    )

    response = client.post(
        url,
        data=json.dumps(
            {
                "query_string": "willkommen",
                "object_type": "page",
            }
        ),
        content_type="application/json",
    )

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert settings.LOGIN_URL in response.headers.get("location", "")
    elif role == EVENT_MANAGER:
        # EVENT_MANAGER does not have view_page permission
        assert response.status_code == 403
    else:
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "suggestions" in data["data"]
        assert isinstance(data["data"]["suggestions"], list)


@pytest.mark.django_db
def test_search_suggest_empty_query_returns_empty(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that empty query returns empty suggestions
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    if role in (ANONYMOUS, EVENT_MANAGER):
        return  # Skip for users without view_page permission

    url = reverse(
        "search_suggest",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": LANGUAGE_SLUG,
        },
    )

    response = client.post(
        url,
        data=json.dumps(
            {
                "query_string": "",
                "object_type": "page",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["suggestions"] == []


@pytest.mark.django_db
def test_search_suggest_missing_object_type_returns_error(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that missing object_type returns 400 error
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    if role == ANONYMOUS:
        return  # Skip for anonymous users

    url = reverse(
        "search_suggest",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": LANGUAGE_SLUG,
        },
    )

    response = client.post(
        url,
        data=json.dumps(
            {
                "query_string": "test",
            }
        ),
        content_type="application/json",
    )

    # Missing object_type returns 400 for all authenticated users
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


@pytest.mark.django_db
def test_search_suggest_contact(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test search suggestions for contacts
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    if role == ANONYMOUS:
        return

    # Contacts don't need language_slug, use region-only URL
    url = reverse(
        "search_suggest",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )

    response = client.post(
        url,
        data=json.dumps(
            {
                "query_string": "test",
                "object_type": "contact",
            }
        ),
        content_type="application/json",
    )

    if role in (EVENT_MANAGER, OBSERVER):
        # EVENT_MANAGER and OBSERVER do not have view_contact permission
        assert response.status_code == 403
    else:
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "suggestions" in data["data"]


@pytest.mark.django_db
def test_search_suggest_suggestions_are_sorted_by_score(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that suggestions are sorted by score in descending order
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    if role in (ANONYMOUS, EVENT_MANAGER):
        return  # Skip for users without view_page permission

    url = reverse(
        "search_suggest",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": LANGUAGE_SLUG,
        },
    )

    response = client.post(
        url,
        data=json.dumps(
            {
                "query_string": "au",  # Broad query to get multiple results
                "object_type": "page",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    suggestions = data["data"]["suggestions"]
    if len(suggestions) > 1:
        scores = [s["score"] for s in suggestions]
        assert scores == sorted(scores, reverse=True), (
            "Suggestions should be sorted by score descending"
        )


@pytest.mark.django_db
def test_search_suggest_filters_by_region(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that search suggestions only return results from the current region.
    Nurnberg has a page titled "Willkommen in Nürnberg!" which should not
    appear in Augsburg search results when searching for "Nürnberg".
    """
    client, role = login_role_user
    settings.LANGUAGE_CODE = "en"

    if role != CMS_TEAM:
        return  # use CMS_TEAM to have access to multiple regions

    # Search for "Nürnberg" in Augsburg - should return no results
    # because Augsburg doesn't have pages with "Nürnberg" in the title,
    # but Nurnberg does (and we want to verify it doesn't leak across regions)
    url = reverse(
        "search_suggest",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": LANGUAGE_SLUG,
        },
    )

    response = client.post(
        url,
        data=json.dumps(
            {
                "query_string": "Nürnberg",
                "object_type": "page",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    suggestions = [s["suggestion"] for s in data["data"]["suggestions"]]

    # Augsburg should not have any suggestions containing "Nürnberg"
    # (Nurnberg region has "Willkommen in Nürnberg!" but it should not appear here)
    assert not any("Nürnberg" in s for s in suggestions), (
        f"Region filtering failed: found 'Nürnberg' in Augsburg suggestions: {suggestions}"
    )

    url = reverse(
        "search_suggest",
        kwargs={
            "region_slug": "nurnberg",
            "language_slug": LANGUAGE_SLUG,
        },
    )

    response = client.post(
        url,
        data=json.dumps(
            {
                "query_string": "Nürnberg",
                "object_type": "page",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    suggestions = [s["suggestion"] for s in data["data"]["suggestions"]]

    # Nürnberg should have suggestions containing Nürnberg
    assert any("Nürnberg" in s for s in suggestions), (
        f"Search suggest failed: Expected Nürnberg in search suggestions, got {suggestions}"
    )
