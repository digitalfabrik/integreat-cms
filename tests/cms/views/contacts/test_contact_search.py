from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.constants import (
    ANONYMOUS,
    AUTHOR,
    EDITOR,
    MANAGEMENT,
    STAFF_ROLES,
)

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"

# Contact ids from test data (all have location in Augsburg, region 1)
# id=1 name="Martina Musterfrau", not archived
# id=3 name="Mariana Musterfrau", not archived
# id=5 name="referred to in a page", not archived

AUTHORIZED_ROLES = [*STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR]


@pytest.mark.django_db
def test_contact_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the contact list filters by name and only shows matching contacts.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("contacts", kwargs={"region_slug": REGION_SLUG})
    response = client.get(url, {"search_query": "Martina"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in AUTHORIZED_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Martina Musterfrau" in content
    assert "Mariana Musterfrau" not in content
