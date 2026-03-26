from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.constants import (
    ANONYMOUS,
    AUTHOR,
    EDITOR,
    MANAGEMENT,
    OBSERVER,
    STAFF_ROLES,
)

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"
LANGUAGE_SLUG = "de"

# Pages in Augsburg test data (German):
# "Willkommen in Augsburg" (page 2)
# "Wissenswertes über Augsburg" (page 4)

AUTHORIZED_ROLES = [*STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR, OBSERVER]


@pytest.mark.django_db
def test_page_tree_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the page tree filters by title and only shows matching pages.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse(
        "pages",
        kwargs={"region_slug": REGION_SLUG, "language_slug": LANGUAGE_SLUG},
    )
    response = client.get(url, {"search_query": "Willkommen"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in AUTHORIZED_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Willkommen" in content
    assert "Wissenswertes" not in content
