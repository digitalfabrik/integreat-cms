"""
Pin the number of database queries of the CMS views which execute the most queries
(see the query report: ``./tools/test.py -- --query-report``).

If a change reduces the number of queries, lower the budget. If it increases the
number, check the query report for new N+1 or duplicate queries before raising it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse

from tests.constants import ROOT

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Final

#: The views with their kwargs and the expected number of queries of a GET request by the root user
QUERY_BUDGETS: Final[list[tuple[str, dict[str, Any], int]]] = [
    ("new_region", {}, 10),
    ("edit_region", {"slug": "augsburg"}, 13),
    ("languagetreenodes", {"region_slug": "augsburg"}, 9),
    ("pages", {"region_slug": "augsburg", "language_slug": "de"}, 26),
    ("new_page", {"region_slug": "augsburg", "language_slug": "de"}, 23),
    (
        "edit_page",
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 4},
        56,
    ),
    ("new_role", {}, 116),
    ("edit_role", {"role_id": 1}, 157),
    ("edit_language", {"slug": "de"}, 64),
    ("linkcheck", {"region_slug": "augsburg", "url_filter": "valid"}, 60),
]


@pytest.mark.django_db
@pytest.mark.parametrize("view_name,kwargs,expected_queries", QUERY_BUDGETS)
def test_query_budget(
    load_test_data: None,
    monkeypatch: pytest.MonkeyPatch,
    django_assert_num_queries: Callable,
    view_name: str,
    kwargs: dict[str, Any],
    expected_queries: int,
) -> None:
    """
    Check that the views in :attr:`QUERY_BUDGETS` do not execute more (or fewer) queries than expected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param monkeypatch: The fixture to reset the machine translation providers
    :param django_assert_num_queries: The fixture providing the query assertion
    :param view_name: The name of the view
    :param kwargs: The kwargs of the view
    :param expected_queries: The expected number of SQL queries
    """
    # Other tests change the supported languages of the providers, which enables the machine translation form
    for provider in ("deepl_api", "google_translate_api"):
        monkeypatch.setattr(
            apps.get_app_config(provider), "supported_target_languages", []
        )
    client = Client()
    client.force_login(get_user_model().objects.get(username=ROOT.lower()))
    url = reverse(view_name, kwargs=kwargs)
    # Warm up process-wide caches (e.g. content types), so the count does not depend on the tests which ran before
    assert client.get(url).status_code == 200
    with django_assert_num_queries(expected_queries):
        response = client.get(url)
    assert response.status_code == 200
