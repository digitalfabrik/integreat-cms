from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.conftest import ANONYMOUS, MANAGEMENT, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"

# Organizations in test data for Augsburg (region 1):
# pk=1 "Nicht archivierte Organisation", archived=False
# pk=2 "Archivierte Organisation",       archived=True
# pk=3 "Not Referenced Organisation",    archived=False

AUTHORIZED_ROLES = [*STAFF_ROLES, MANAGEMENT]


@pytest.mark.django_db
def test_organization_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the organization list filters by name and only shows matching organizations.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("organizations", kwargs={"region_slug": REGION_SLUG})
    response = client.get(url, {"search_query": "Nicht"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in AUTHORIZED_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Nicht archivierte Organisation" in content
    assert "Not Referenced Organisation" not in content
