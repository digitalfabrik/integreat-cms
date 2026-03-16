from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.conftest import ANONYMOUS, MANAGEMENT, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"
LANGUAGE_SLUG = "de"

# Push notifications for Augsburg (region 1) with their DE translations:
# pk=1 title="Test DE", pk=2 title="Nicht gesendet", pk=3 title="Mehrere Regionen",
# pk=4 title="Terminierte Nachricht", pk=5 title="Vorlage", pk=8 title="German Message"

AUTHORIZED_ROLES = [*STAFF_ROLES, MANAGEMENT]


@pytest.mark.django_db
def test_push_notification_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the push notification list filters by title and only shows matching notifications.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse(
        "push_notifications",
        kwargs={"region_slug": REGION_SLUG, "language_slug": LANGUAGE_SLUG},
    )
    response = client.get(url, {"search_query": "Nicht gesendet"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in AUTHORIZED_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Nicht gesendet" in content
    assert "Terminierte Nachricht" not in content
