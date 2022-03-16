from urllib.parse import urlencode

import pytest

from django.urls import reverse


# pylint: disable=unused-argument,too-many-locals
@pytest.mark.django_db
def test_page_filters(load_test_data, admin_client):
    """
    Test whether duplicating regions works as expected

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple

    :param admin_client: The fixture providing the logged in admin
    :type admin_client: :fixture:`admin_client`
    """
    page_tree = reverse(
        "pages", kwargs={"region_slug": "augsburg", "language_slug": "en"}
    )
    # Get with no data should result in the normal, unfiltered view with only root pages
    response = admin_client.get(page_tree)
    print(response.headers)
    assert response.status_code == 200
    # Root pages should be in the result
    assert "Welcome" in response.content.decode("utf-8")
    # Sub-pages should not be in the result
    assert "Trivia about Augsburg" not in response.content.decode("utf-8")
    assert "About the Integreat App Augsburg" not in response.content.decode("utf-8")
    # Searching for a page should return all results, independently of their level
    filter_params = {"query": "Augsburg"}
    response = admin_client.get(f"{page_tree}?{urlencode(filter_params)}")
    print(response.headers)
    assert response.status_code == 200
    # Pages without the query in the title should not be in the result
    assert "Welcome" not in response.content.decode("utf-8")
    # Pages with the query in the title should be in the result
    assert "Trivia about Augsburg" in response.content.decode("utf-8")
    assert "About the Integreat App Augsburg" in response.content.decode("utf-8")
    # Test filtering for the translation status
    filter_params = {"translation_status": ["OUTDATED", "MISSING"]}
    response = admin_client.get(f"{page_tree}?{urlencode(filter_params, True)}")
    print(f"{page_tree}?{urlencode(filter_params, True)}")
    print(response.headers)
    assert response.status_code == 200
    # Up-to-date pages should not be in the result
    assert "Welcome" not in response.content.decode("utf-8")
    # Missing and outdated pages should be in the result
    assert "Trivia about Augsburg" in response.content.decode("utf-8")
    assert "About the Integreat App Augsburg" in response.content.decode("utf-8")
    # Test filtering for the translation status and searching at the same time
    filter_params = {"query": "Trivia", "translation_status": ["OUTDATED", "MISSING"]}
    response = admin_client.get(f"{page_tree}?{urlencode(filter_params, True)}")
    print(response.headers)
    assert response.status_code == 200
    # Up-to-date pages should not be in the result
    assert "Welcome" not in response.content.decode("utf-8")
    # Missing and outdated pages with "Trivia" in the title should be in the result
    assert "Trivia about Augsburg" in response.content.decode("utf-8")
    # Missing and outdated pages without "Trivia" should not be in the result
    assert "About the Integreat App Augsburg" not in response.content.decode("utf-8")
    # Test filtering for the translation status and searching at the same time
    filter_params = {"query": "Welco", "translation_status": ["OUTDATED", "MISSING"]}
    response = admin_client.get(f"{page_tree}?{urlencode(filter_params, True)}")
    print(response.headers)
    assert response.status_code == 200
    # Up-to-date pages should not be in the result, even if they contain "Welco" in the title
    assert "Welcome" not in response.content.decode("utf-8")
    # Missing and outdated pages without "Welco" should not be in the result
    assert "Trivia about Augsburg" not in response.content.decode("utf-8")
    assert "About the Integreat App Augsburg" not in response.content.decode("utf-8")
