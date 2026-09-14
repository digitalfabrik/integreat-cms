from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.constants import ANONYMOUS, MANAGEMENT, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"

# Feedback comments in test data:
# "Region feedback unread and not archived" (pk 4, region feedback, not archived)
# "Region feedback read and not archived" (pk 6, region feedback, not archived)
# "Feedback unread and not archived" (pk 1, admin/technical feedback, not archived)
# "Feedback read and not archived" (pk 3, admin/technical feedback, not archived)


@pytest.mark.django_db
def test_region_feedback_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the region feedback list filters by comment.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("region_feedback", kwargs={"region_slug": REGION_SLUG})
    response = client.get(url, {"search_query": "unread"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in [*STAFF_ROLES, MANAGEMENT]:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "unread" in content.lower()
    assert "Region feedback read and not archived" not in content


@pytest.mark.django_db
def test_admin_feedback_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the admin feedback list filters by comment.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("admin_feedback")
    response = client.get(url, {"search_query": "unread"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in STAFF_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "unread" in content.lower()
    assert "Feedback read and not archived" not in content
