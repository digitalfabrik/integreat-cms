from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.conftest import ANONYMOUS, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

"""
Active/Hidden regions in test data (the only ones shown in region condition view):
Augsburg (ACTIVE), Nürnberg (ACTIVE), hallo aschaffenburg (HIDDEN),
Artland (ACTIVE), Testumgebung (HIDDEN), Berlin (ACTIVE)
Excluded (ARCHIVED): Birkenfeld, Region without language
"""


@pytest.mark.django_db
def test_region_condition_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the region condition view filters by name and only shows matching regions.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("region_condition")
    response = client.get(url, {"search_query": "Augsburg"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in STAFF_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    # In the table row template the href attribute is the last attribute on its line,
    # so the closing > follows directly: href="/augsburg/">. In the nav region selector
    # the href is followed by a newline and a class attribute, so href="/augsburg/"
    # is never immediately followed by >. This distinguishes table rows from nav links.
    assert 'href="/augsburg/">' in content
    assert 'href="/berlin/">' not in content
