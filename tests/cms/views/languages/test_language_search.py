from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.conftest import ANONYMOUS, STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

# Languages in test data (english_name / native_name):
# German/Deutsch, English/English, Arabic/العربية, Farsi/فارسی,
# Spanish/Español, German (easy)/Deutsch (leicht), Hidden language/Hidden language, Amharic/አማርኛ


@pytest.mark.django_db
def test_language_list_search_filters_results(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that searching the language list filters by english_name/native_name and only shows matches.
    Regression test: after the search form switched from POST to GET, views that still
    read from request.POST returned unfiltered results.
    """
    client, role = login_role_user

    url = reverse("languages")
    response = client.get(url, {"search_query": "Farsi"})

    if role == ANONYMOUS:
        assert response.status_code == 302
        return

    if role not in STAFF_ROLES:
        assert response.status_code in (302, 403)
        return

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Farsi" in content
    assert "Español" not in content

    # empty search should find all languages
    response = client.get(url, {})
    content = response.content.decode("utf-8")
    assert "Español" in content
