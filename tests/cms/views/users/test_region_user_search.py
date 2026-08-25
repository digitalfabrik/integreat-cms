from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.constants import ANONYMOUS, MANAGEMENT, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"

# Users belonging to Augsburg (region 1):
# username="management"    first_name="Region"       last_name="Manager"
# username="editor"        first_name="Region"       last_name="Editor"
# username="event_manager" first_name="Region Event" last_name="Manager"
# username="author"        first_name="Region"       last_name="Author"
# username="observer"      first_name="Region"       last_name="Observer"

AUTHORIZED_ROLES = [*STAFF_ROLES, MANAGEMENT]


@pytest.mark.django_db
def test_region_user_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the region user list filters by username/name and only shows matching users.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("region_users", kwargs={"region_slug": REGION_SLUG})
    response = client.get(url, {"search_query": "Author"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in AUTHORIZED_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "author" in content
    assert "editor" not in content
