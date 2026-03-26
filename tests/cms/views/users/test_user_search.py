from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.constants import ANONYMOUS, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

# Network-level users in test data:
# "root", "service_team", "cms_team", "app_team", "marketing_team"


@pytest.mark.django_db
def test_user_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the user list filters by username/name and only shows matching users.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("users")
    response = client.get(url, {"search_query": "root"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in STAFF_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "root" in content
    assert "service_team" not in content
