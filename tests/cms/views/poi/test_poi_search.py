from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.conftest import ANONYMOUS, ROLES

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"
LANGUAGE_SLUG = "de"

# POIs in Augsburg (region 1) with their DE translations:
# pk=4 title="Test-Ort"    (not archived)
# pk=6 title="Entwurf-Ort" (not archived)


@pytest.mark.django_db
def test_poi_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the POI list filters by translation title and only shows matching POIs.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse(
        "pois",
        kwargs={"region_slug": REGION_SLUG, "language_slug": LANGUAGE_SLUG},
    )
    response = client.get(url, {"search_query": "Entwurf"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Entwurf-Ort" in content
    assert "Test-Ort" not in content
