from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.conftest import ANONYMOUS, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

# Regions in test data: Augsburg, Nürnberg, hallo aschaffenburg, Artland, Birkenfeld,
# Testumgebung, Region without language, Berlin


@pytest.mark.django_db
def test_region_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the region list filters by name and only shows matching regions.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("regions")
    response = client.get(url, {"search_query": "Augsburg"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in STAFF_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    # Edit links only appear in table rows, not in the nav region selector
    assert "/regions/augsburg/edit/" in content
    assert "/regions/berlin/edit/" not in content
